from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
import requests
import json
import os
from dotenv import load_dotenv
import time
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from pydantic import BaseModel, Field, field_validator

# Pydantic models for input validation
class PaperRetrievalInput(BaseModel):
    keywords: Optional[List[str]] = Field(None, description="List of keywords to search for in paper titles and abstracts")
    authors: Optional[List[str]] = Field(None, description="List of author names to search for")
    topics: Optional[List[str]] = Field(None, description="List of topics to filter papers by")
    year: Optional[int] = Field(None, description="Publication year to filter papers by")
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError('Year must be between 1900 and 2100')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "keywords": ["quantum computing", "artificial intelligence"],
                "authors": ["Yoshua Bengio"],
                "topics": ["machine learning"],
                "year": 2023
            }
        }
    }

class DatasetExplorerInput(BaseModel):
    dataset_id: str = Field(..., description="ID or URL of the dataset to analyze")
    analysis_type: str = Field("summary", description="Type of analysis to perform (summary, distribution, correlation)")
    
    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        allowed_types = ["summary", "distribution", "correlation"]
        if v not in allowed_types:
            raise ValueError(f"Analysis type must be one of: {', '.join(allowed_types)}")
        return v

class CitationNetworkInput(BaseModel):
    paper_ids: List[str] = Field(..., description="List of paper IDs to analyze")
    analysis_depth: int = Field(1, description="Depth of citation analysis (1-3)")
    
    @field_validator('analysis_depth')
    @classmethod
    def validate_depth(cls, v):
        if v < 1 or v > 3:
            raise ValueError('Analysis depth must be between 1 and 3')
        return v

class ConceptExtractorInput(BaseModel):
    paper_ids: Optional[List[str]] = Field(None, description="List of paper IDs to extract concepts from")
    text: Optional[str] = Field(None, description="Text to extract concepts from")
    
    @field_validator('paper_ids', 'text')
    @classmethod
    def validate_input(cls, v, info):
        field_name = info.field_name
        if field_name == 'paper_ids' and v is None and info.data.get('text') is None:
            raise ValueError('Either paper_ids or text must be provided')
        if field_name == 'text' and v is None and info.data.get('paper_ids') is None:
            raise ValueError('Either paper_ids or text must be provided')
        return v

class CrossDomainConnectorInput(BaseModel):
    domain1: str = Field(..., description="First domain or field")
    domain2: str = Field(..., description="Second domain or field")

# Output models
class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    year: int
    categories: List[str]
    pdf_link: str

class PaperRetrievalOutput(BaseModel):
    papers: List[Paper]
    count: int
    query_params: Dict[str, Any]

# Load environment variables
load_dotenv()

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the MCP server
mcp = FastMCP("ResearchAssistantAgent")

# Helper function to handle API errors
def handle_api_error(response):
    try:
        return response.json(), response.status_code
    except:
        return {"error": f"Failed to decode response. Status code: {response.status_code}"}, response.status_code

@mcp.tool()
async def paper_retrieval_tool(keywords: Optional[List[str]] = None, 
                              authors: Optional[List[str]] = None, 
                              topics: Optional[List[str]] = None, 
                              year: Optional[int] = None) -> dict:
    """
    Fetches scientific papers based on keywords, authors, or topics.
    
    Args:
        keywords: List of keywords to search for in paper titles and abstracts
        authors: List of author names to search for
        topics: List of topics to filter papers by
        year: Publication year to filter papers by
    
    Returns:
        A dictionary containing matching papers
    """
    # Validate input using Pydantic model
    input_data = PaperRetrievalInput(
        keywords=keywords,
        authors=authors,
        topics=topics,
        year=year
    )
    
    try:
        # Create query string for arXiv API
        query_parts = []
        
        if input_data.keywords:
            keyword_query = " OR ".join([f"\"{keyword}\"" for keyword in input_data.keywords])
            query_parts.append(f"(ti:{keyword_query} OR abs:{keyword_query})")
            
        if input_data.authors:
            author_query = " OR ".join([f"au:\"{author}\"" for author in input_data.authors])
            query_parts.append(f"({author_query})")
            
        if input_data.topics:
            # Map topics to arXiv categories if possible (simplified)
            category_map = {
                "physics": "physics",
                "mathematics": "math",
                "computer science": "cs",
                "quantitative biology": "q-bio",
                "quantitative finance": "q-fin",
                "statistics": "stat",
                "electrical engineering": "eess",
                "economics": "econ"
            }
            
            category_parts = []
            for topic in input_data.topics:
                topic_lower = topic.lower()
                for key, value in category_map.items():
                    if key in topic_lower:
                        category_parts.append(f"cat:{value}*")
                        break
            
            if category_parts:
                query_parts.append(f"({' OR '.join(category_parts)})")
        
        # Combine all query parts with AND
        query = " AND ".join(query_parts) if query_parts else "all:electron"  # default search if nothing specified
        
        # Add year if specified (using submission date)
        if input_data.year:
            query += f" AND submittedDate:[{input_data.year}0101 TO {input_data.year}1231]"
        
        # Call the arXiv API
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": 10,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        response = requests.get(base_url, params=params)
        
        # Process the response - this is XML by default, so we'll convert to a simple format
        import xml.etree.ElementTree as ET
        from datetime import datetime
        
        if response.status_code == 200:
            # Parse XML response
            root = ET.fromstring(response.text)
            namespace = {"arxiv": "http://www.w3.org/2005/Atom"}
            
            # Extract papers
            papers = []
            for entry in root.findall(".//arxiv:entry", namespace):
                paper_id = entry.find("arxiv:id", namespace).text
                title = entry.find("arxiv:title", namespace).text.replace("\n", " ").strip()
                abstract = entry.find("arxiv:summary", namespace).text.replace("\n", " ").strip()
                published = entry.find("arxiv:published", namespace).text
                
                # Format the published date
                pub_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                year = pub_date.year
                
                # Get authors
                author_elements = entry.findall(".//arxiv:author/arxiv:name", namespace)
                authors = [author.text for author in author_elements]
                
                # Get categories/topics
                category_elements = entry.findall(".//arxiv:category", namespace)
                categories = [cat.get("term") for cat in category_elements]
                
                # Get PDF link
                pdf_link = f"https://arxiv.org/pdf/{paper_id.split('/')[-1]}.pdf"
                
                papers.append({
                    "id": paper_id,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "year": year,
                    "categories": categories,
                    "pdf_link": pdf_link
                })
            
            # Validate output data
            output_data = PaperRetrievalOutput(
                papers=papers,
                count=len(papers),
                query_params={
                    "keywords": input_data.keywords,
                    "authors": input_data.authors,
                    "topics": input_data.topics,
                    "year": input_data.year
                }
            )
            
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=json.dumps(output_data.model_dump(), indent=2, ensure_ascii=False)
                    )
                ]
            }
        else:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"ArXiv API error: {response.status_code}",
                            "message": response.text
                        }, indent=2)
                    )
                ]
            }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e)
                    }, indent=2)
                )
            ]
        }

@mcp.tool()
async def dataset_explorer_tool(dataset_id: str, analysis_type: str = "summary") -> dict:
    """
    Analyzes and extracts insights from datasets.
    
    Args:
        dataset_id: ID or URL of the dataset to analyze
        analysis_type: Type of analysis to perform (summary, distribution, correlation)
    
    Returns:
        A dictionary containing analysis results
    """
    # Validate input using Pydantic model
    input_data = DatasetExplorerInput(
        dataset_id=dataset_id,
        analysis_type=analysis_type
    )
    
    try:
        # For this demo, we'll use the data.gov API to get dataset information
        if input_data.dataset_id.startswith("http"):
            # If it's a URL, use it directly
            dataset_url = input_data.dataset_id
        else:
            # Otherwise search for the dataset
            search_url = f"https://catalog.data.gov/api/3/action/package_search"
            params = {
                "q": input_data.dataset_id,
                "rows": 1
            }
            
            search_response = requests.get(search_url, params=params)
            if search_response.status_code != 200:
                return {
                    "content": [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"Dataset search failed: {search_response.status_code}",
                                "message": search_response.text
                            }, indent=2)
                        )
                    ]
                }
            
            search_data = search_response.json()
            if not search_data.get("result", {}).get("results"):
                return {
                    "content": [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": "No datasets found matching the ID",
                                "message": "Try using a more specific ID or a direct URL"
                            }, indent=2)
                        )
                    ]
                }
            
            dataset_info = search_data["result"]["results"][0]
            dataset_url = dataset_info.get("url", "")
        
        # Get metadata about the dataset
        dataset_metadata = {
            "id": input_data.dataset_id,
            "url": dataset_url,
            "analysis_type": input_data.analysis_type
        }
        
        # For a more realistic implementation, you would fetch and analyze the actual dataset here
        # For example, using pandas to load a CSV and compute statistics
        
        # Simulate different analysis types
        analysis_results = {}
        
        if input_data.analysis_type == "summary":
            analysis_results = {
                "dataset_info": dataset_metadata,
                "summary": {
                    "estimated_rows": "1,000+",
                    "estimated_columns": "10+",
                    "data_types": ["numerical", "categorical", "temporal"],
                    "description": "Dataset contains multiple variables suitable for statistical analysis."
                }
            }
        elif input_data.analysis_type == "distribution":
            analysis_results = {
                "dataset_info": dataset_metadata,
                "distributions": {
                    "note": "To perform actual distribution analysis, the dataset would need to be downloaded and analyzed using statistical tools.",
                    "expected_distributions": [
                        "Normal distributions for continuous variables",
                        "Skewed distributions for count data",
                        "Categorical distributions for nominal variables"
                    ]
                }
            }
        elif input_data.analysis_type == "correlation":
            analysis_results = {
                "dataset_info": dataset_metadata,
                "correlations": {
                    "note": "To perform correlation analysis, the dataset would need to be downloaded and analyzed using statistical tools.",
                    "correlation_methods": [
                        "Pearson correlation for continuous variables",
                        "Spearman rank correlation for ordinal variables",
                        "Chi-squared tests for categorical variables"
                    ]
                }
            }
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps(analysis_results, indent=2)
                )
            ]
        }
        
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e)
                    }, indent=2)
                )
            ]
        }

@mcp.tool()
async def citation_network_analyzer(paper_ids: List[str], analysis_depth: int = 1) -> dict:
    """
    Maps relationships between papers and identifies research clusters.
    
    Args:
        paper_ids: List of paper IDs to analyze
        analysis_depth: Depth of citation analysis (1-3)
    
    Returns:
        A dictionary containing citation network analysis
    """
    # Validate input using Pydantic model
    input_data = CitationNetworkInput(
        paper_ids=paper_ids,
        analysis_depth=analysis_depth
    )
    
    try:
        # For this implementation, we'll use the Semantic Scholar API
        # This is free but has rate limits
        papers_data = []
        network_nodes = {}
        network_edges = []
        
        # Limit analysis depth to avoid excessive API calls
        analysis_depth = min(input_data.analysis_depth, 3)
        
        # Process each paper ID
        for paper_id in input_data.paper_ids:
            # Clean up the paper ID
            if paper_id.startswith("http"):
                # Extract the ID from the URL
                paper_id = paper_id.split("/")[-1]
            
            # Call Semantic Scholar API
            api_url = f"https://api.semanticscholar.org/v1/paper/{paper_id}"
            headers = {"Accept": "application/json"}
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                paper_data = response.json()
                
                # Add to papers data
                papers_data.append({
                    "id": paper_data.get("paperId", paper_id),
                    "title": paper_data.get("title", "Unknown Title"),
                    "authors": [author.get("name") for author in paper_data.get("authors", [])],
                    "year": paper_data.get("year"),
                    "venue": paper_data.get("venue"),
                    "citation_count": paper_data.get("citationCount", 0)
                })
                
                # Add to network data
                paper_node_id = paper_data.get("paperId", paper_id)
                network_nodes[paper_node_id] = {
                    "id": paper_node_id,
                    "title": paper_data.get("title", "Unknown Title"),
                    "year": paper_data.get("year"),
                    "citation_count": paper_data.get("citationCount", 0)
                }
                
                # Add citation edges
                if analysis_depth > 0:
                    # Add cited papers (outgoing edges)
                    for reference in paper_data.get("references", [])[:5]:  # Limit to 5 to avoid too many requests
                        ref_id = reference.get("paperId")
                        if ref_id:
                            network_edges.append({
                                "source": paper_node_id,
                                "target": ref_id,
                                "type": "cites"
                            })
                            
                            if ref_id not in network_nodes:
                                network_nodes[ref_id] = {
                                    "id": ref_id,
                                    "title": reference.get("title", "Unknown Title"),
                                    "year": reference.get("year")
                                }
                    
                    # Add citing papers (incoming edges)
                    if analysis_depth > 1:
                        for citation in paper_data.get("citations", [])[:5]:  # Limit to 5
                            cit_id = citation.get("paperId")
                            if cit_id:
                                network_edges.append({
                                    "source": cit_id,
                                    "target": paper_node_id,
                                    "type": "cites"
                                })
                                
                                if cit_id not in network_nodes:
                                    network_nodes[cit_id] = {
                                        "id": cit_id,
                                        "title": citation.get("title", "Unknown Title"),
                                        "year": citation.get("year")
                                    }
        
        # Prepare the results
        network_analysis = {
            "papers": papers_data,
            "network": {
                "nodes": list(network_nodes.values()),
                "edges": network_edges
            },
            "query_params": {
                "paper_ids": input_data.paper_ids,
                "analysis_depth": input_data.analysis_depth
            }
        }
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps(network_analysis, indent=2)
                )
            ]
        }
        
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e)
                    }, indent=2)
                )
            ]
        }

@mcp.tool()
async def concept_extractor(paper_ids: List[str] = None, text: str = None) -> dict:
    """
    Identifies key concepts and terminology across papers or in provided text using LLM.
    
    Args:
        paper_ids: List of paper IDs to analyze
        text: Text to analyze if paper_ids is not provided
    
    Returns:
        A dictionary containing extracted concepts
    """
    # Validate input using Pydantic model
    input_data = ConceptExtractorInput(
        paper_ids=paper_ids,
        text=text
    )
    
    try:
        # Initialize Gemini Flash model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # If paper_ids are provided, fetch their abstracts first
        combined_text = ""
        papers_data = []
        
        if input_data.paper_ids and not input_data.text:
            for paper_id in input_data.paper_ids:
                # Clean up the paper ID if it's an arXiv URL
                if "arxiv.org" in paper_id:
                    paper_id = paper_id.split("/")[-1]
                    if paper_id.endswith(".pdf"):
                        paper_id = paper_id[:-4]
                    
                    # Call arXiv API
                    api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
                    response = requests.get(api_url)
                    
                    if response.status_code == 200:
                        import xml.etree.ElementTree as ET
                        
                        # Parse XML
                        root = ET.fromstring(response.text)
                        namespace = {"arxiv": "http://www.w3.org/2005/Atom"}
                        
                        # Find the entry for this paper
                        entry = root.find(".//arxiv:entry", namespace)
                        if entry:
                            title = entry.find("arxiv:title", namespace).text.replace("\n", " ").strip()
                            abstract = entry.find("arxiv:summary", namespace).text.replace("\n", " ").strip()
                            
                            # Add to combined text
                            combined_text += f"{title}. {abstract} "
                            
                            # Add to papers data
                            papers_data.append({
                                "id": paper_id,
                                "title": title,
                                "abstract": abstract
                            })
                # Sleep to respect API rate limits
                time.sleep(1)
        elif input_data.text:
            combined_text = input_data.text
        else:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Either paper_ids or text must be provided"
                        }, indent=2)
                    )
                ]
            }
        
        # Use LLM for concept extraction instead of traditional NLP methods
        prompt = """Analyze the following text from scientific papers or documents. Extract and categorize the key concepts, terminology, and themes.

TEXT TO ANALYZE:
""" + combined_text + """

Please output your analysis as a JSON object with the following structure:
{
  "keywords": [
    {"term": "keyword1", "score": 0.95, "importance": "high"},
    {"term": "keyword2", "score": 0.85, "importance": "high"},
    ...
  ],
  "concept_categories": {
    "technical": [list of technical terms and concepts],
    "methodological": [list of methodological terms],
    "domain-specific": [list of domain-specific terms],
    "general": [list of general concepts]
  },
  "key_themes": [list of overarching themes],
  "relationships": [list of relationships between concepts]
}

Be sure the output is valid JSON that can be parsed. Only include the JSON object, no other text.
"""
        
        # Call the LLM
        response = model.generate_content(prompt)
        
        try:
            # Clean LLM response text to handle markdown code blocks
            response_text = response.text.strip()
            if response_text.startswith("```"):
                # Remove opening code block marker (```json or just ```)
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                else:
                    response_text = response_text[3:]
                    
                # Remove closing code block marker if present
                if "```" in response_text:
                    response_text = response_text.rsplit("```", 1)[0]
                
            response_text = response_text.strip()
            
            # Parse the LLM response
            analysis = json.loads(response_text)
            
            # Add paper data if we have it
            if papers_data:
                analysis["papers"] = papers_data
            
            # Add document summary
            analysis["document_summary"] = {
                "text_length": len(combined_text),
                "keyword_count": len(analysis.get("keywords", [])),
                "category_count": len(analysis.get("concept_categories", {}))
            }
            
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=json.dumps(analysis, indent=2)
                    )
                ]
            }
            
        except json.JSONDecodeError:
            # If LLM didn't return valid JSON, extract what we can
            text_response = response.text
            
            # Simple fallback: extract what looks like keywords
            import re
            potential_keywords = re.findall(r'"term":\s*"([^"]+)"', text_response)
            
            fallback_analysis = {
                "papers": papers_data,
                "keywords": [{"term": keyword, "score": 0.5} for keyword in potential_keywords[:15]],
                "error": "Could not parse LLM output as valid JSON",
                "document_summary": {
                    "text_length": len(combined_text),
                    "keyword_count": len(potential_keywords)
                }
            }
            
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=json.dumps(fallback_analysis, indent=2)
                    )
                ]
            }
            
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e)
                    }, indent=2)
                )
            ]
        }

@mcp.tool()
async def cross_domain_connector(domain1: str, domain2: str) -> dict:
    """
    Finds unexpected connections between different research domains.
    
    Args:
        domain1: First domain name
        domain2: Second domain name
    
    Returns:
        A dictionary containing connections between domains
    """
    # Validate input using Pydantic model
    input_data = CrossDomainConnectorInput(
        domain1=domain1,
        domain2=domain2
    )
    
    try:
        # For this implementation, we'll use arXiv to find papers that bridge both domains
        
        # Map domain names to potential arXiv categories or search terms
        domains = {
            input_data.domain1: input_data.domain1.lower(),
            input_data.domain2: input_data.domain2.lower()
        }
        
        # Create a search query for papers that mention both domains
        search_query = f"all:({domains[input_data.domain1]} AND {domains[input_data.domain2]})"
        
        # Call arXiv API
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": search_query,
            "max_results": 10,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            
            # Parse XML
            root = ET.fromstring(response.text)
            namespace = {"arxiv": "http://www.w3.org/2005/Atom"}
            
            # Get all matching papers
            bridging_papers = []
            for entry in root.findall(".//arxiv:entry", namespace):
                paper_id = entry.find("arxiv:id", namespace).text
                title = entry.find("arxiv:title", namespace).text.replace("\n", " ").strip()
                abstract = entry.find("arxiv:summary", namespace).text.replace("\n", " ").strip()
                published = entry.find("arxiv:published", namespace).text
                
                # Get authors
                author_elements = entry.findall(".//arxiv:author/arxiv:name", namespace)
                authors = [author.text for author in author_elements]
                
                # Get categories
                category_elements = entry.findall(".//arxiv:category", namespace)
                categories = [cat.get("term") for cat in category_elements]
                
                # Get PDF link
                pdf_link = f"https://arxiv.org/pdf/{paper_id.split('/')[-1]}.pdf"
                
                bridging_papers.append({
                    "id": paper_id,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "categories": categories,
                    "pdf_link": pdf_link
                })
            
            # Use LLM to identify potential connections between domains
            if bridging_papers:
                paper_titles = "\n".join([f"- {paper['title']}" for paper in bridging_papers[:5]])
                abstracts = "\n\n".join([paper["abstract"] for paper in bridging_papers[:3]])
                
                # Initialize Gemini Flash model for analysis
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                prompt = f"""Analyze the connections between the domains of {input_data.domain1} and {input_data.domain2} based on these recent papers that bridge both fields:

Paper Titles:
{paper_titles}

Sample abstracts:
{abstracts}

Please identify:
1. Key bridging concepts that connect these domains
2. Methodologies or techniques that transfer between domains
3. Potential future research opportunities at this intersection
4. Challenges in connecting these domains

Format your response as a JSON object:
{{
  "bridging_concepts": [list of concepts with brief descriptions],
  "transferable_methods": [list of methodologies],
  "research_opportunities": [list of potential research directions],
  "challenges": [list of challenges],
  "unexpected_connections": [list of any surprising or non-obvious connections you notice]
}}
"""
                
                # Call the LLM
                response = model.generate_content(prompt)
                
                try:
                    # Clean LLM response text to handle markdown code blocks
                    response_text = response.text.strip()
                    if response_text.startswith("```"):
                        # Remove opening code block marker (```json or just ```)
                        if response_text.startswith("```json"):
                            response_text = response_text[7:]
                        else:
                            response_text = response_text[3:]
                            
                        # Remove closing code block marker if present
                        if "```" in response_text:
                            response_text = response_text.rsplit("```", 1)[0]
                        
                    response_text = response_text.strip()
                    
                    # Parse the LLM response
                    analysis = json.loads(response_text)
                    
                    # Combine everything into one response
                    result = {
                        "domains": {
                            "domain1": input_data.domain1,
                            "domain2": input_data.domain2
                        },
                        "bridging_papers": bridging_papers,
                        "domain_connections": analysis
                    }
                    
                    return {
                        "content": [
                            TextContent(
                                type="text",
                                text=json.dumps(result, indent=2)
                            )
                        ]
                    }
                    
                except json.JSONDecodeError:
                    # If LLM response isn't valid JSON, return a more basic response
                    result = {
                        "domains": {
                            "domain1": input_data.domain1,
                            "domain2": input_data.domain2
                        },
                        "bridging_papers": bridging_papers,
                        "note": "Found papers that connect both domains. LLM analysis failed to produce valid JSON."
                    }
                    
                    return {
                        "content": [
                            TextContent(
                                type="text",
                                text=json.dumps(result, indent=2)
                            )
                        ]
                    }
            else:
                return {
                    "content": [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "domains": {
                                    "domain1": input_data.domain1,
                                    "domain2": input_data.domain2
                                },
                                "result": "No papers found that connect both domains"
                            }, indent=2)
                        )
                    ]
                }
        else:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"ArXiv API error: {response.status_code}",
                            "message": response.text
                        }, indent=2)
                    )
                ]
            }
            
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e)
                    }, indent=2)
                )
            ]
        }

# Run the server
if __name__ == "__main__":
    mcp.run() 