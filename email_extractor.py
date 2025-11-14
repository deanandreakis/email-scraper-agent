"""
Email extraction utilities for finding and validating email addresses from text.
"""

import re
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from loguru import logger


@dataclass
class EmailData:
    """Data class for storing email information."""
    email: str
    source_url: str
    found_at: datetime
    confidence: float
    context: Optional[str] = None


class EmailExtractor:
    """Extract and validate email addresses from text content."""

    # Comprehensive email regex pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    )

    # Patterns to exclude (common false positives)
    EXCLUDE_PATTERNS = [
        r'.*@example\.(com|org|net)',
        r'.*@domain\.(com|org|net)',
        r'.*@test\.(com|org|net)',
        r'.*@placeholder\.',
        r'.*@yourdomain\.',
        r'.*@yourcompany\.',
        r'.*@email\.(com|org|net)',
        r'.*\.png@',
        r'.*\.jpg@',
        r'.*\.gif@',
        r'.*\.svg@',
    ]

    # Common disposable/temporary email domains to filter
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'throwaway.email', 'guerrillamail.com',
        'mailinator.com', '10minutemail.com', 'trashmail.com'
    }

    def __init__(self, validate_dns: bool = True, min_confidence: float = 0.7):
        """
        Initialize the email extractor.

        Args:
            validate_dns: Whether to perform DNS validation
            min_confidence: Minimum confidence score to accept an email
        """
        self.validate_dns = validate_dns
        self.min_confidence = min_confidence
        self._compile_exclude_patterns()

    def _compile_exclude_patterns(self):
        """Compile exclusion patterns for efficiency."""
        self.exclude_compiled = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.EXCLUDE_PATTERNS
        ]

    def extract_from_text(
        self,
        text: str,
        source_url: str,
        include_context: bool = False
    ) -> List[EmailData]:
        """
        Extract emails from text content.

        Args:
            text: Text content to extract from
            source_url: Source URL where the text was found
            include_context: Whether to include surrounding context

        Returns:
            List of EmailData objects
        """
        if not text:
            return []

        emails = []
        matches = self.EMAIL_PATTERN.finditer(text)

        for match in matches:
            email = match.group(0).lower()

            # Skip if excluded pattern
            if self._is_excluded(email):
                continue

            # Validate and calculate confidence
            is_valid, confidence = self._validate_and_score(email)

            if is_valid and confidence >= self.min_confidence:
                context = None
                if include_context:
                    context = self._extract_context(text, match.start(), match.end())

                emails.append(EmailData(
                    email=email,
                    source_url=source_url,
                    found_at=datetime.now(),
                    confidence=confidence,
                    context=context
                ))

        return emails

    def _is_excluded(self, email: str) -> bool:
        """Check if email matches exclusion patterns."""
        # Check against exclude patterns
        for pattern in self.exclude_compiled:
            if pattern.match(email):
                return True

        # Check against disposable domains
        domain = email.split('@')[1] if '@' in email else ''
        if domain in self.DISPOSABLE_DOMAINS:
            return True

        return False

    def _validate_and_score(self, email: str) -> tuple[bool, float]:
        """
        Validate email and calculate confidence score.

        Returns:
            Tuple of (is_valid, confidence_score)
        """
        confidence = 0.5  # Base confidence

        try:
            # Basic email validation
            validation = validate_email(email, check_deliverability=self.validate_dns)
            normalized_email = validation.normalized

            # Increase confidence based on various factors

            # Has common TLD
            if email.endswith(('.com', '.org', '.net', '.edu', '.gov')):
                confidence += 0.2

            # Not too long
            if len(email) < 50:
                confidence += 0.1

            # Has reasonable local part (before @)
            local_part = email.split('@')[0]
            if 3 <= len(local_part) <= 30:
                confidence += 0.1

            # No suspicious patterns
            if not re.search(r'\d{5,}', email):  # No long number sequences
                confidence += 0.1

            return True, min(confidence, 1.0)

        except EmailNotValidError as e:
            logger.debug(f"Invalid email {email}: {e}")
            return False, 0.0

    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract context around the email address."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        context = text[context_start:context_end].strip()
        return context

    def deduplicate(self, emails: List[EmailData]) -> List[EmailData]:
        """
        Remove duplicate emails, keeping the one with highest confidence.

        Args:
            emails: List of EmailData objects

        Returns:
            Deduplicated list of EmailData objects
        """
        email_dict: Dict[str, EmailData] = {}

        for email_data in emails:
            email = email_data.email

            if email not in email_dict:
                email_dict[email] = email_data
            else:
                # Keep the one with higher confidence
                if email_data.confidence > email_dict[email].confidence:
                    email_dict[email] = email_data

        return list(email_dict.values())

    def filter_by_domain(self, emails: List[EmailData], domains: List[str]) -> List[EmailData]:
        """
        Filter emails by allowed domains.

        Args:
            emails: List of EmailData objects
            domains: List of allowed domains

        Returns:
            Filtered list of EmailData objects
        """
        if not domains:
            return emails

        filtered = []
        for email_data in emails:
            domain = email_data.email.split('@')[1] if '@' in email_data.email else ''
            if any(domain.endswith(d) for d in domains):
                filtered.append(email_data)

        return filtered

    def extract_from_html(self, html: str, source_url: str) -> List[EmailData]:
        """
        Extract emails from HTML content, including from mailto links.

        Args:
            html: HTML content
            source_url: Source URL

        Returns:
            List of EmailData objects
        """
        from bs4 import BeautifulSoup

        emails = []

        # Extract from text content
        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text()
        emails.extend(self.extract_from_text(text, source_url))

        # Extract from mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            href = link.get('href', '')
            match = re.search(r'mailto:([^\?&]+)', href, re.I)
            if match:
                email = match.group(1).lower()
                if not self._is_excluded(email):
                    is_valid, confidence = self._validate_and_score(email)
                    if is_valid and confidence >= self.min_confidence:
                        emails.append(EmailData(
                            email=email,
                            source_url=source_url,
                            found_at=datetime.now(),
                            confidence=min(confidence + 0.1, 1.0),  # Boost for mailto
                            context="mailto link"
                        ))

        return self.deduplicate(emails)


def main():
    """Example usage of EmailExtractor."""
    extractor = EmailExtractor(validate_dns=False, min_confidence=0.7)

    sample_text = """
    Contact us at info@example.com or support@company.org.
    You can also reach our sales team at sales@company.org.
    For technical issues, email tech@test.com (this should be excluded).
    """

    emails = extractor.extract_from_text(sample_text, "https://example.com")

    print(f"Found {len(emails)} emails:")
    for email_data in emails:
        print(f"  - {email_data.email} (confidence: {email_data.confidence:.2f})")


if __name__ == "__main__":
    main()
