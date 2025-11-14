"""
Google Agent Development Kit integration for intelligent website discovery.
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import google.generativeai as genai
from loguru import logger


@dataclass
class WebsiteCandidate:
    """Data class for website candidates."""
    url: str
    relevance_score: float
    description: str
    category: str


class GoogleSearchAgent:
    """AI agent using Google's Generative AI for website discovery."""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """
        Initialize the Google Search Agent.

        Args:
            api_key: Google API key
            model: Model name to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        logger.info(f"Initialized Google Agent with model: {model}")

    def analyze_topic(self, topic: str) -> Dict[str, any]:
        """
        Analyze a topic to understand what websites to search for.

        Args:
            topic: Topic or classification to analyze

        Returns:
            Dictionary with topic analysis
        """
        logger.info(f"Analyzing topic: {topic}")

        prompt = f"""
        Analyze the following topic/classification and provide a structured analysis:

        Topic: "{topic}"

        Provide your analysis in JSON format with the following structure:
        {{
            "topic_summary": "Brief summary of the topic",
            "key_categories": ["list", "of", "relevant", "categories"],
            "search_keywords": ["list", "of", "search", "keywords"],
            "typical_domains": ["example domains that would fit this topic"],
            "industry": "primary industry classification"
        }}

        Only respond with valid JSON, no additional text.
        """

        try:
            response = self.model.generate_content(prompt)
            analysis = json.loads(self._extract_json(response.text))
            logger.info(f"Topic analysis complete: {analysis.get('industry', 'Unknown')}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing topic: {e}")
            # Return default analysis
            return {
                "topic_summary": topic,
                "key_categories": [topic],
                "search_keywords": [topic],
                "typical_domains": [],
                "industry": "General"
            }

    def generate_website_candidates(
        self,
        topic: str,
        num_websites: int = 10,
        country: str = "US",
        language: str = "en"
    ) -> List[WebsiteCandidate]:
        """
        Generate a list of candidate websites for the given topic.

        Args:
            topic: Topic or classification
            num_websites: Number of websites to generate
            country: Country code
            language: Language code

        Returns:
            List of WebsiteCandidate objects
        """
        logger.info(f"Generating {num_websites} website candidates for topic: {topic}")

        prompt = f"""
        You are an expert at finding relevant websites for business and research purposes.

        Topic/Classification: "{topic}"
        Country: {country}
        Language: {language}
        Number of websites needed: {num_websites}

        Generate a list of real, legitimate websites that match this topic. These should be:
        - Real, publicly accessible websites
        - Relevant to the topic
        - Likely to have contact information (emails)
        - Professional business or organization websites

        Provide your response in JSON format:
        {{
            "websites": [
                {{
                    "url": "https://example.com",
                    "relevance_score": 0.95,
                    "description": "Brief description of the website",
                    "category": "Primary category"
                }}
            ]
        }}

        Only respond with valid JSON, no additional text.
        Include exactly {num_websites} websites.
        """

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(self._extract_json(response.text))

            candidates = []
            for item in data.get("websites", []):
                candidates.append(WebsiteCandidate(
                    url=item["url"],
                    relevance_score=item["relevance_score"],
                    description=item["description"],
                    category=item["category"]
                ))

            logger.info(f"Generated {len(candidates)} website candidates")
            return candidates

        except Exception as e:
            logger.error(f"Error generating website candidates: {e}")
            return []

    def generate_search_queries(self, topic: str, num_queries: int = 5) -> List[str]:
        """
        Generate search queries for finding websites related to the topic.

        Args:
            topic: Topic or classification
            num_queries: Number of queries to generate

        Returns:
            List of search query strings
        """
        logger.info(f"Generating {num_queries} search queries for: {topic}")

        prompt = f"""
        Generate {num_queries} effective Google search queries to find websites related to this topic:

        Topic: "{topic}"

        The queries should be designed to find:
        - Business websites in this industry
        - Organizations related to this topic
        - Companies offering services in this area
        - Professional associations

        Format your response as a JSON list:
        {{
            "queries": ["query 1", "query 2", "query 3"]
        }}

        Only respond with valid JSON, no additional text.
        """

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(self._extract_json(response.text))
            queries = data.get("queries", [])
            logger.info(f"Generated {len(queries)} search queries")
            return queries

        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            # Return default queries
            return [
                f"{topic} companies",
                f"{topic} organizations",
                f"{topic} services",
                f"{topic} contact"
            ]

    def filter_and_rank_websites(
        self,
        topic: str,
        websites: List[str]
    ) -> List[WebsiteCandidate]:
        """
        Filter and rank a list of websites by relevance to the topic.

        Args:
            topic: Topic or classification
            websites: List of website URLs

        Returns:
            Ranked list of WebsiteCandidate objects
        """
        logger.info(f"Filtering and ranking {len(websites)} websites for topic: {topic}")

        # Process in batches to avoid token limits
        batch_size = 20
        all_candidates = []

        for i in range(0, len(websites), batch_size):
            batch = websites[i:i + batch_size]

            prompt = f"""
            Analyze and rank these websites by their relevance to the topic: "{topic}"

            Websites:
            {json.dumps(batch, indent=2)}

            For each website, provide:
            - Relevance score (0.0 to 1.0)
            - Brief description
            - Category classification

            Respond in JSON format:
            {{
                "ranked_websites": [
                    {{
                        "url": "website url",
                        "relevance_score": 0.95,
                        "description": "description",
                        "category": "category"
                    }}
                ]
            }}

            Only include websites with relevance_score >= 0.5.
            Only respond with valid JSON, no additional text.
            """

            try:
                response = self.model.generate_content(prompt)
                data = json.loads(self._extract_json(response.text))

                for item in data.get("ranked_websites", []):
                    all_candidates.append(WebsiteCandidate(
                        url=item["url"],
                        relevance_score=item["relevance_score"],
                        description=item["description"],
                        category=item["category"]
                    ))

            except Exception as e:
                logger.error(f"Error ranking batch: {e}")

        # Sort by relevance score
        all_candidates.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(f"Filtered to {len(all_candidates)} relevant websites")
        return all_candidates

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that might contain markdown or other formatting.

        Args:
            text: Text potentially containing JSON

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def suggest_alternative_topics(self, topic: str, num_suggestions: int = 5) -> List[str]:
        """
        Suggest alternative or related topics.

        Args:
            topic: Original topic
            num_suggestions: Number of suggestions

        Returns:
            List of alternative topic suggestions
        """
        prompt = f"""
        Suggest {num_suggestions} alternative or related topics to: "{topic}"

        These should be:
        - Related but distinct topics
        - More specific or broader variations
        - Adjacent industries or categories

        Respond in JSON format:
        {{
            "suggestions": ["topic 1", "topic 2", "topic 3"]
        }}

        Only respond with valid JSON, no additional text.
        """

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(self._extract_json(response.text))
            return data.get("suggestions", [])

        except Exception as e:
            logger.error(f"Error suggesting topics: {e}")
            return []


def main():
    """Example usage of GoogleSearchAgent."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set")
        return

    agent = GoogleSearchAgent(api_key)

    # Analyze a topic
    topic = "healthcare technology startups"
    analysis = agent.analyze_topic(topic)
    print(f"\nTopic Analysis:")
    print(json.dumps(analysis, indent=2))

    # Generate website candidates
    candidates = agent.generate_website_candidates(topic, num_websites=5)
    print(f"\nWebsite Candidates:")
    for candidate in candidates:
        print(f"  - {candidate.url} (score: {candidate.relevance_score:.2f})")
        print(f"    {candidate.description}")

    # Generate search queries
    queries = agent.generate_search_queries(topic, num_queries=3)
    print(f"\nSearch Queries:")
    for query in queries:
        print(f"  - {query}")


if __name__ == "__main__":
    main()
