"""Unit tests for PDF parsing functionality in ingestion service."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.parsers.ual_pdf import Leg, Trip as UALTrip
from app.services.ingestion import IngestionService, PDFParsingError
from app.services.pbs_parser.contracts import Pairing


class TestPDFParsing:
    """Test cases for PDF parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = IngestionService()

    def test_extract_pdf_text_success(self):
        """Test successful PDF text extraction."""
        # Mock PDF content
        mock_pdf_content = b"%PDF-1.4\n%Mock PDF content"

        with patch("pypdf.PdfReader") as mock_reader:
            # Mock the PDF reader and page
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample trip data"

            mock_pdf_reader = MagicMock()
            mock_pdf_reader.pages = [mock_page]
            mock_reader.return_value = mock_pdf_reader

            result = self.service._extract_pdf_text(mock_pdf_content)

            assert result == "Sample trip data\n"
            mock_reader.assert_called_once()

    def test_extract_pdf_text_empty_content(self):
        """Test PDF text extraction with empty content."""
        mock_pdf_content = b"%PDF-1.4\n%Mock PDF content"

        with patch("pypdf.PdfReader") as mock_reader:
            # Mock the PDF reader with empty text
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""

            mock_pdf_reader = MagicMock()
            mock_pdf_reader.pages = [mock_page]
            mock_reader.return_value = mock_pdf_reader

            with pytest.raises(PDFParsingError, match="No text content found in PDF"):
                self.service._extract_pdf_text(mock_pdf_content)

    def test_extract_pdf_text_import_error(self):
        """Test PDF text extraction with missing pypdf library."""
        mock_pdf_content = b"%PDF-1.4\n%Mock PDF content"

        with patch("pypdf.PdfReader", side_effect=ImportError):
            with pytest.raises(PDFParsingError, match="pypdf library not installed"):
                self.service._extract_pdf_text(mock_pdf_content)

    def test_extract_pdf_text_parsing_error(self):
        """Test PDF text extraction with parsing error."""
        mock_pdf_content = b"Invalid PDF content"

        with patch("pypdf.PdfReader", side_effect=Exception("Invalid PDF")):
            with pytest.raises(PDFParsingError, match="Failed to extract text from PDF"):
                self.service._extract_pdf_text(mock_pdf_content)

    def test_convert_to_pairings_success(self):
        """Test successful conversion of UAL trips to pairings."""
        # Create mock UAL trips
        leg1 = Leg(
            flight="1234",
            departure_airport="SFO",
            arrival_airport="LAX",
            departure=datetime.now(),
            arrival=datetime.now(),
            equipment="737",
        )
        leg2 = Leg(
            flight="5678",
            departure_airport="LAX",
            arrival_airport="SFO",
            departure=datetime.now(),
            arrival=datetime.now(),
            equipment="737",
        )

        ual_trip = UALTrip(trip_id="T001", credit=12.5, legs=[leg1, leg2])

        result = self.service._convert_to_pairings([ual_trip], "test.pdf")

        assert len(result) == 1
        pairing = result[0]
        assert isinstance(pairing, Pairing)
        assert pairing.pairing_id == "PDF-T001"
        assert pairing.base == "SFO"
        assert pairing.fleet == "737"
        assert len(pairing.trips) == 2

        # Check the converted trips
        trip1 = pairing.trips[0]
        assert trip1.trip_id == "T001-L1"
        assert trip1.pairing_id == "PDF-T001"
        assert trip1.day == 1
        assert trip1.origin == "SFO"
        assert trip1.destination == "LAX"

    def test_convert_to_pairings_empty_trips(self):
        """Test conversion with empty UAL trips list."""
        result = self.service._convert_to_pairings([], "test.pdf")
        assert len(result) == 0

    def test_convert_to_pairings_trip_without_legs(self):
        """Test conversion with UAL trip that has no legs."""
        ual_trip = UALTrip(trip_id="T001", credit=12.5, legs=[])

        result = self.service._convert_to_pairings([ual_trip], "test.pdf")

        assert len(result) == 1
        pairing = result[0]
        assert pairing.pairing_id == "PDF-T001"
        assert pairing.base == "UNK"  # Default when no legs
        assert pairing.fleet == "UNK"  # Default when no equipment
        assert len(pairing.trips) == 0

    @patch("app.services.ingestion.IngestionService._extract_pdf_text")
    @patch("app.parsers.ual_pdf._parse_text")
    def test_parse_pdf_success(self, mock_parse_text, mock_extract_text):
        """Test successful PDF parsing end-to-end."""
        # Setup mocks
        mock_extract_text.return_value = "Sample PDF text content"

        leg = Leg(
            flight="1234",
            departure_airport="SFO",
            arrival_airport="LAX",
            departure=datetime.now(),
            arrival=datetime.now(),
            equipment="737",
        )

        ual_trip = UALTrip(trip_id="T001", credit=12.5, legs=[leg])

        mock_parse_text.return_value = [ual_trip]

        # Test the method
        result = self.service._parse_pdf(b"mock pdf content", "test.pdf")

        # Verify calls
        mock_extract_text.assert_called_once_with(b"mock pdf content")
        mock_parse_text.assert_called_once_with("Sample PDF text content")

        # Verify result
        assert len(result) == 1
        assert isinstance(result[0], Pairing)
        assert result[0].pairing_id == "PDF-T001"

    @patch("app.services.ingestion.IngestionService._extract_pdf_text")
    def test_parse_pdf_extraction_error(self, mock_extract_text):
        """Test PDF parsing with text extraction error."""
        mock_extract_text.side_effect = Exception("PDF extraction failed")

        with pytest.raises(PDFParsingError, match="Failed to parse PDF test.pdf"):
            self.service._parse_pdf(b"mock pdf content", "test.pdf")

    @patch("app.services.ingestion.IngestionService._extract_pdf_text")
    @patch("app.parsers.ual_pdf._parse_text")
    def test_parse_pdf_parsing_error(self, mock_parse_text, mock_extract_text):
        """Test PDF parsing with UAL parser error."""
        mock_extract_text.return_value = "Sample PDF text content"
        mock_parse_text.side_effect = ValueError("No trips found")

        with pytest.raises(PDFParsingError, match="Failed to parse PDF test.pdf"):
            self.service._parse_pdf(b"mock pdf content", "test.pdf")

    @patch("app.services.ingestion.IngestionService._extract_pdf_text")
    @patch("app.parsers.ual_pdf._parse_text")
    def test_parse_pdf_conversion_error(self, mock_parse_text, mock_extract_text):
        """Test PDF parsing with conversion error."""
        mock_extract_text.return_value = "Sample PDF text content"
        mock_parse_text.return_value = [{"invalid": "object"}]  # Not a UAL Trip object

        # This should not raise an error, but should handle gracefully
        result = self.service._parse_pdf(b"mock pdf content", "test.pdf")
        assert len(result) == 0  # No valid trips converted
