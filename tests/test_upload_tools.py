"""Tests for file upload tools."""

import pytest
import base64
from pathlib import Path

from registry_review_mcp.tools import upload_tools, session_tools
from registry_review_mcp.models.errors import SessionNotFoundError


@pytest.fixture
def sample_pdf_base64():
    """Create a minimal test PDF encoded as base64."""
    # Minimal valid PDF structure
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Times-Roman\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000074 00000 n\n0000000120 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n149\n%%EOF"
    return base64.b64encode(pdf_content).decode('utf-8')


@pytest.fixture
def sample_text_base64():
    """Create a simple text file encoded as base64."""
    text_content = b"This is a test document for the registry review system."
    return base64.b64encode(text_content).decode('utf-8')


@pytest.fixture
def sample_pdf2_base64():
    """Create a different minimal PDF encoded as base64 (with different content)."""
    # Different PDF with unique content to avoid deduplication
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Different Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000074 00000 n\n0000000120 00000 n\n0000000298 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n393\n%%EOF"
    return base64.b64encode(pdf_content).decode('utf-8')


@pytest.fixture
def sample_pdf3_base64():
    """Create a third different minimal PDF encoded as base64."""
    # Another unique PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Courier\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Third File Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000074 00000 n\n0000000120 00000 n\n0000000296 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n391\n%%EOF"
    return base64.b64encode(pdf_content).decode('utf-8')


class TestSanitizeProjectName:
    """Test project name sanitization."""

    def test_sanitize_basic_name(self):
        """Test basic project name sanitization."""
        result = upload_tools._sanitize_project_name("Botany Farm 2022")
        assert result == "botany-farm-2022"

    def test_sanitize_special_chars(self):
        """Test sanitization removes special characters."""
        result = upload_tools._sanitize_project_name("Project @#$% Name!")
        assert result == "project-name"

    def test_sanitize_multiple_spaces(self):
        """Test multiple spaces become single hyphens."""
        result = upload_tools._sanitize_project_name("Project    Name")
        assert result == "project-name"

    def test_sanitize_leading_trailing_hyphens(self):
        """Test leading/trailing hyphens are removed."""
        result = upload_tools._sanitize_project_name("  Project Name  ")
        assert result == "project-name"


class TestCreateSessionFromUploads:
    """Test create_session_from_uploads business logic."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, test_settings, sample_pdf_base64):
        """Test successful session creation from uploads."""
        result = await upload_tools.create_session_from_uploads(
            project_name="Test Project",
            files=[
                {
                    "filename": "test.pdf",
                    "content_base64": sample_pdf_base64,
                    "mime_type": "application/pdf"
                }
            ],
            methodology="soil-carbon-v1.2.2"
        )

        # Verify result structure
        assert result["success"] is True
        assert "session_id" in result
        assert result["session_id"].startswith("session-")
        assert result["files_saved"] == ["test.pdf"]
        assert result["documents_found"] >= 1
        assert "temp_directory" in result

        # Verify temp directory was created and contains file
        temp_dir = Path(result["temp_directory"])
        assert temp_dir.exists()
        assert (temp_dir / "test.pdf").exists()

        # Cleanup
        try:
            await session_tools.delete_session(result["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_create_session_multiple_files(
        self, test_settings, sample_pdf_base64, sample_pdf2_base64, sample_text_base64
    ):
        """Test creating session with multiple files."""
        result = await upload_tools.create_session_from_uploads(
            project_name="Multi File Test",
            files=[
                {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
                {"filename": "file2.txt", "content_base64": sample_text_base64},
                {"filename": "file3.pdf", "content_base64": sample_pdf2_base64},  # Use different PDF
            ],
        )

        assert result["success"] is True
        assert len(result["files_saved"]) == 3
        assert "file1.pdf" in result["files_saved"]
        assert "file2.txt" in result["files_saved"]
        assert "file3.pdf" in result["files_saved"]

        # Cleanup
        try:
            await session_tools.delete_session(result["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_create_session_missing_project_name(self, test_settings):
        """Test error when project_name is missing."""
        with pytest.raises(ValueError, match="project_name is required"):
            await upload_tools.create_session_from_uploads(
                project_name="",
                files=[{"filename": "test.pdf", "content_base64": "abc"}]
            )

    @pytest.mark.asyncio
    async def test_create_session_missing_project_name_whitespace(self, test_settings):
        """Test error when project_name is only whitespace."""
        with pytest.raises(ValueError, match="project_name is required"):
            await upload_tools.create_session_from_uploads(
                project_name="   ",
                files=[{"filename": "test.pdf", "content_base64": "abc"}]
            )

    @pytest.mark.asyncio
    async def test_create_session_no_files(self, test_settings):
        """Test error when files array is empty."""
        with pytest.raises(ValueError, match="At least one file is required"):
            await upload_tools.create_session_from_uploads(
                project_name="Test",
                files=[]
            )

    @pytest.mark.asyncio
    async def test_create_session_missing_filename(self, test_settings, sample_pdf_base64):
        """Test error when file is missing filename."""
        with pytest.raises(ValueError, match="missing 'filename'"):
            await upload_tools.create_session_from_uploads(
                project_name="Test",
                files=[{"content_base64": sample_pdf_base64}]
            )

    @pytest.mark.asyncio
    async def test_create_session_missing_content(self, test_settings):
        """Test error when file is missing both content_base64 and path."""
        with pytest.raises(ValueError, match="must have either 'content_base64' or 'path' field"):
            await upload_tools.create_session_from_uploads(
                project_name="Test",
                files=[{"filename": "test.pdf"}]
            )

    @pytest.mark.asyncio
    async def test_create_session_invalid_base64(self, test_settings):
        """Test error when base64 content is invalid."""
        with pytest.raises(ValueError, match="Failed to decode base64"):
            await upload_tools.create_session_from_uploads(
                project_name="Test",
                files=[{"filename": "test.pdf", "content_base64": "not-valid-base64!!!"}]
            )

    @pytest.mark.asyncio
    async def test_create_session_with_all_metadata(self, test_settings, sample_pdf_base64):
        """Test session creation with all optional metadata."""
        result = await upload_tools.create_session_from_uploads(
            project_name="Full Metadata Test",
            files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}],
            methodology="soil-carbon-v1.2.2",
            project_id="C06-1234",
            proponent="Test Proponent Inc.",
            crediting_period="2022-2032",
        )

        assert result["success"] is True

        # Load session and verify metadata
        session_data = await session_tools.load_session(result["session_id"])
        assert session_data["project_metadata"]["project_id"] == "C06-1234"
        assert session_data["project_metadata"]["proponent"] == "Test Proponent Inc."
        assert session_data["project_metadata"]["crediting_period"] == "2022-2032"

        # Cleanup
        try:
            await session_tools.delete_session(result["session_id"])
        except:
            pass


class TestUploadAdditionalFiles:
    """Test upload_additional_files business logic."""

    @pytest.mark.asyncio
    async def test_upload_additional_files_success(self, test_settings, sample_pdf_base64, sample_pdf2_base64):
        """Test adding files to existing session."""
        # First create a session
        session_result = await upload_tools.create_session_from_uploads(
            project_name="Test Project",
            files=[{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
        )

        session_id = session_result["session_id"]

        try:
            # Add another file with different content
            result = await upload_tools.upload_additional_files(
                session_id=session_id,
                files=[{"filename": "file2.pdf", "content_base64": sample_pdf2_base64}]
            )

            assert result["success"] is True
            assert result["session_id"] == session_id
            assert result["files_added"] == ["file2.pdf"]
            assert result["documents_found"] >= 2

            # Verify file was written
            session_data = await session_tools.load_session(session_id)
            docs_path = Path(session_data["project_metadata"]["documents_path"])
            assert (docs_path / "file2.pdf").exists()

        finally:
            await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_upload_additional_multiple_files(self, test_settings, sample_pdf_base64, sample_pdf2_base64, sample_pdf3_base64):
        """Test adding multiple files at once."""
        # Create session
        session_result = await upload_tools.create_session_from_uploads(
            project_name="Test",
            files=[{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
        )

        session_id = session_result["session_id"]

        try:
            # Add multiple files with different content
            result = await upload_tools.upload_additional_files(
                session_id=session_id,
                files=[
                    {"filename": "file2.pdf", "content_base64": sample_pdf2_base64},
                    {"filename": "file3.pdf", "content_base64": sample_pdf3_base64},
                ]
            )

            assert len(result["files_added"]) == 2
            assert "file2.pdf" in result["files_added"]
            assert "file3.pdf" in result["files_added"]
            assert result["documents_found"] >= 3

        finally:
            await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_upload_additional_files_duplicate_filename(self, test_settings, sample_pdf_base64):
        """Test error when uploading file with duplicate filename."""
        # Create session with file1.pdf
        session_result = await upload_tools.create_session_from_uploads(
            project_name="Test",
            files=[{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
        )

        session_id = session_result["session_id"]

        try:
            # Try to add another file1.pdf
            with pytest.raises(ValueError, match="File already exists"):
                await upload_tools.upload_additional_files(
                    session_id=session_id,
                    files=[{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
                )

        finally:
            await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_upload_additional_files_session_not_found(self, test_settings, sample_pdf_base64):
        """Test error when session doesn't exist."""
        with pytest.raises(SessionNotFoundError):
            await upload_tools.upload_additional_files(
                session_id="nonexistent-session-id",
                files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}]
            )

    @pytest.mark.asyncio
    async def test_upload_additional_files_no_files(self, test_settings, sample_pdf_base64):
        """Test error when files array is empty."""
        # Create session
        session_result = await upload_tools.create_session_from_uploads(
            project_name="Test",
            files=[{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
        )

        session_id = session_result["session_id"]

        try:
            with pytest.raises(ValueError, match="At least one file is required"):
                await upload_tools.upload_additional_files(
                    session_id=session_id,
                    files=[]
                )

        finally:
            await session_tools.delete_session(session_id)


class TestStartReviewFromUploads:
    """Test start_review_from_uploads business logic."""

    @pytest.mark.asyncio
    async def test_start_review_full_workflow(self, test_settings, sample_pdf_base64, sample_pdf2_base64):
        """Test complete review workflow with auto-extraction."""
        result = await upload_tools.start_review_from_uploads(
            project_name="Full Test",
            files=[
                {"filename": "ProjectPlan.pdf", "content_base64": sample_pdf_base64},
                {"filename": "BaselineReport.pdf", "content_base64": sample_pdf2_base64}  # Use different PDF
            ],
            auto_extract=True
        )

        assert "session_creation" in result
        assert "evidence_extraction" in result

        session_result = result["session_creation"]
        assert session_result["success"] is True
        assert len(session_result["files_saved"]) == 2
        assert "ProjectPlan.pdf" in session_result["files_saved"]
        assert "BaselineReport.pdf" in session_result["files_saved"]

        # Evidence extraction may succeed or fail gracefully
        evidence = result["evidence_extraction"]
        assert evidence is not None

        # Cleanup
        try:
            await session_tools.delete_session(session_result["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_start_review_no_auto_extract(self, test_settings, sample_pdf_base64):
        """Test workflow without auto-extraction."""
        result = await upload_tools.start_review_from_uploads(
            project_name="No Extract Test",
            files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}],
            auto_extract=False
        )

        assert "session_creation" in result
        assert "evidence_extraction" not in result  # Should not extract

        # Cleanup
        try:
            await session_tools.delete_session(result["session_creation"]["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_start_review_with_metadata(self, test_settings, sample_pdf_base64):
        """Test start review with all metadata fields."""
        result = await upload_tools.start_review_from_uploads(
            project_name="Metadata Test",
            files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}],
            methodology="soil-carbon-v1.2.2",
            project_id="C06-5678",
            proponent="Test Org",
            crediting_period="2023-2033",
            auto_extract=False
        )

        session_result = result["session_creation"]
        assert session_result["success"] is True

        # Verify metadata was passed through
        session_data = await session_tools.load_session(session_result["session_id"])
        assert session_data["project_metadata"]["project_id"] == "C06-5678"
        assert session_data["project_metadata"]["proponent"] == "Test Org"
        assert session_data["project_metadata"]["crediting_period"] == "2023-2033"

        # Cleanup
        try:
            await session_tools.delete_session(session_result["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_start_review_invalid_inputs(self, test_settings):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError, match="project_name is required"):
            await upload_tools.start_review_from_uploads(
                project_name="",
                files=[{"filename": "test.pdf", "content_base64": "abc"}]
            )

        with pytest.raises(ValueError, match="At least one file is required"):
            await upload_tools.start_review_from_uploads(
                project_name="Test",
                files=[]
            )


class TestDeduplication:
    """Test file deduplication functionality."""

    def test_deduplicate_by_filename_basic(self):
        """Test filename deduplication."""
        files = [
            {"filename": "file1.pdf", "content_base64": "AAAA"},
            {"filename": "file2.pdf", "content_base64": "BBBB"},
            {"filename": "file1.pdf", "content_base64": "CCCC"},  # Duplicate filename
        ]

        unique, duplicates = upload_tools.deduplicate_by_filename(files)

        assert len(unique) == 2
        assert len(duplicates) == 1
        assert duplicates[0] == "file1.pdf"
        assert unique[0]["filename"] == "file1.pdf"
        assert unique[1]["filename"] == "file2.pdf"

    def test_deduplicate_by_filename_with_existing(self):
        """Test filename deduplication with existing files."""
        files = [
            {"filename": "file1.pdf", "content_base64": "AAAA"},
            {"filename": "file2.pdf", "content_base64": "BBBB"},
        ]
        existing = {"file2.pdf", "file3.pdf"}

        unique, duplicates = upload_tools.deduplicate_by_filename(files, existing)

        assert len(unique) == 1
        assert len(duplicates) == 1
        assert duplicates[0] == "file2.pdf"
        assert unique[0]["filename"] == "file1.pdf"

    def test_deduplicate_by_content(self, sample_pdf_base64):
        """Test content-based deduplication."""
        files = [
            {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
            {"filename": "file2.pdf", "content_base64": sample_pdf_base64},  # Same content
            {"filename": "file3.pdf", "content_base64": "ZGlmZmVyZW50"},  # Different
        ]

        unique, duplicates_map = upload_tools.deduplicate_by_content(files)

        assert len(unique) == 2
        assert "file2.pdf" in duplicates_map
        assert duplicates_map["file2.pdf"] == "file1.pdf"
        assert unique[0]["filename"] == "file1.pdf"
        assert unique[1]["filename"] == "file3.pdf"

    def test_deduplicate_by_content_all_unique(self, sample_pdf_base64, sample_pdf2_base64):
        """Test content deduplication when all files are unique."""
        files = [
            {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
            {"filename": "file2.pdf", "content_base64": sample_pdf2_base64},
        ]

        unique, duplicates_map = upload_tools.deduplicate_by_content(files)

        assert len(unique) == 2
        assert len(duplicates_map) == 0

    def test_deduplicate_by_content_invalid_base64(self):
        """Test content deduplication with invalid base64."""
        files = [
            {"filename": "file1.pdf", "content_base64": "invalid!!!"},
            {"filename": "file2.pdf", "content_base64": "ZGlmZmVyZW50"},
        ]

        unique, duplicates_map = upload_tools.deduplicate_by_content(files)

        # Invalid base64 is treated as unique
        assert len(unique) == 2
        assert len(duplicates_map) == 0

    @pytest.mark.asyncio
    async def test_create_session_with_duplicates(self, test_settings, sample_pdf_base64):
        """Test that duplicates are automatically removed."""
        result = await upload_tools.create_session_from_uploads(
            project_name="Dedup Test",
            files=[
                {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
                {"filename": "file1.pdf", "content_base64": sample_pdf_base64},  # Dup filename
                {"filename": "file2.pdf", "content_base64": sample_pdf_base64},  # Dup content
            ],
            deduplicate=True
        )

        assert result["success"] is True
        assert result["files_uploaded"] == 3
        assert len(result["files_saved"]) == 1  # Only 1 unique file
        assert result["deduplication"]["enabled"] is True
        assert result["deduplication"]["total_duplicates_removed"] == 2
        assert "file1.pdf" in result["deduplication"]["duplicate_filenames_skipped"]
        assert "file2.pdf" in result["deduplication"]["duplicate_content_detected"]

        # Cleanup
        try:
            await session_tools.delete_session(result["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_create_session_deduplication_disabled(self, test_settings, sample_pdf_base64):
        """Test creating session with deduplication disabled."""
        result = await upload_tools.create_session_from_uploads(
            project_name="No Dedup Test",
            files=[
                {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
                {"filename": "file2.pdf", "content_base64": sample_pdf_base64},
            ],
            deduplicate=False
        )

        assert result["success"] is True
        assert len(result["files_saved"]) == 2  # Both files saved
        assert result["deduplication"]["enabled"] is False
        assert result["deduplication"]["total_duplicates_removed"] == 0

        # Cleanup
        try:
            await session_tools.delete_session(result["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_create_session_all_same_content(self, test_settings, sample_pdf_base64):
        """Test that same content with different filenames keeps one file."""
        result = await upload_tools.create_session_from_uploads(
            project_name="Same Content Test",
            files=[
                {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
                {"filename": "file2.pdf", "content_base64": sample_pdf_base64},  # Same content
                {"filename": "file3.pdf", "content_base64": sample_pdf_base64},  # Same content
            ],
            deduplicate=True
        )

        # Should keep 1 file (the first one) and remove 2 duplicates
        assert result["success"] is True
        assert result["files_uploaded"] == 3
        assert len(result["files_saved"]) == 1
        assert result["deduplication"]["total_duplicates_removed"] == 2

        # Cleanup
        try:
            await session_tools.delete_session(result["session_id"])
        except:
            pass

    @pytest.mark.asyncio
    async def test_start_review_with_deduplication(
        self, test_settings, sample_pdf_base64, sample_pdf2_base64
    ):
        """Test start_review_from_uploads with deduplication."""
        result = await upload_tools.start_review_from_uploads(
            project_name="Review Dedup Test",
            files=[
                {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
                {"filename": "file2.pdf", "content_base64": sample_pdf2_base64},
                {"filename": "file1.pdf", "content_base64": sample_pdf_base64},  # Dup
            ],
            deduplicate=True,
            auto_extract=False
        )

        session_result = result["session_creation"]
        assert session_result["success"] is True
        assert session_result["files_uploaded"] == 3
        assert len(session_result["files_saved"]) == 2
        assert session_result["deduplication"]["total_duplicates_removed"] == 1

        # Cleanup
        try:
            await session_tools.delete_session(session_result["session_id"])
        except:
            pass



class TestSessionDetection:
    """Test automatic session detection (Phase 2)."""

    @pytest.mark.asyncio
    async def test_detect_existing_session_basic(self, test_settings, sample_pdf_base64):
        """Test that existing session is detected for same files."""
        # Create initial session
        result1 = await upload_tools.create_session_from_uploads(
            project_name="Test Project",
            files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}]
        )
        session1_id = result1["session_id"]

        try:
            # Try to create again with same files - should detect existing
            result2 = await upload_tools.create_session_from_uploads(
                project_name="Test Project",  # Same name
                files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}],  # Same file
                force_new_session=False  # Default: detect existing
            )

            assert result2["existing_session_detected"] is True
            assert result2["session_id"] == session1_id
            assert "Found existing session" in result2["message"]

        finally:
            await session_tools.delete_session(session1_id)

    @pytest.mark.asyncio
    async def test_force_new_session_override(self, test_settings, sample_pdf_base64):
        """Test that force_new_session creates new session despite existing match."""
        # Create initial session
        result1 = await upload_tools.create_session_from_uploads(
            project_name="Force Test",
            files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}]
        )
        session1_id = result1["session_id"]

        try:
            # Force create new session with same files
            result2 = await upload_tools.create_session_from_uploads(
                project_name="Force Test",
                files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}],
                force_new_session=True  # Override detection
            )

            # Should create NEW session, not return existing
            assert "existing_session_detected" not in result2 or result2.get("existing_session_detected") is False
            assert result2["session_id"] != session1_id
            assert result2["success"] is True

            # Cleanup second session too
            await session_tools.delete_session(result2["session_id"])

        finally:
            await session_tools.delete_session(session1_id)



class TestPathBasedUploads:
    """Test path-based file upload functionality (Phase 3)."""

    @pytest.fixture
    def temp_pdf_file(self, tmp_path, sample_pdf_base64):
        """Create a temporary PDF file for testing path-based uploads."""
        pdf_path = tmp_path / "test_document.pdf"
        pdf_content = base64.b64decode(sample_pdf_base64)
        pdf_path.write_bytes(pdf_content)
        return pdf_path

    @pytest.fixture
    def temp_pdf_file2(self, tmp_path, sample_pdf2_base64):
        """Create a second temporary PDF file."""
        pdf_path = tmp_path / "test_document2.pdf"
        pdf_content = base64.b64decode(sample_pdf2_base64)
        pdf_path.write_bytes(pdf_content)
        return pdf_path

    def test_process_file_input_base64_format(self, sample_pdf_base64):
        """Test process_file_input with base64 format."""
        file_obj = {
            "filename": "test.pdf",
            "content_base64": sample_pdf_base64
        }

        result = upload_tools.process_file_input(file_obj, 0)

        assert result["filename"] == "test.pdf"
        assert result["content_base64"] == sample_pdf_base64

    def test_process_file_input_path_format(self, temp_pdf_file, sample_pdf_base64):
        """Test process_file_input with path format."""
        file_obj = {
            "filename": "test.pdf",
            "path": str(temp_pdf_file)
        }

        result = upload_tools.process_file_input(file_obj, 0)

        assert result["filename"] == "test.pdf"
        assert result["content_base64"] == sample_pdf_base64

    def test_process_file_input_name_field_compatibility(self, temp_pdf_file):
        """Test that 'name' field works as alternative to 'filename' (ElizaOS compatibility)."""
        file_obj = {
            "name": "test.pdf",
            "path": str(temp_pdf_file)
        }

        result = upload_tools.process_file_input(file_obj, 0)

        assert result["filename"] == "test.pdf"

    def test_process_file_input_missing_filename(self):
        """Test error when both filename and name are missing."""
        file_obj = {
            "content_base64": "abc123"
        }

        with pytest.raises(ValueError, match="missing 'filename' or 'name' field"):
            upload_tools.process_file_input(file_obj, 0)

    def test_process_file_input_missing_content_and_path(self):
        """Test error when neither content_base64 nor path is provided."""
        file_obj = {
            "filename": "test.pdf"
        }

        with pytest.raises(ValueError, match="must have either 'content_base64' or 'path' field"):
            upload_tools.process_file_input(file_obj, 0)

    def test_process_file_input_relative_path_rejected(self, tmp_path):
        """Test that relative paths are rejected for security."""
        file_obj = {
            "filename": "test.pdf",
            "path": "relative/path/to/file.pdf"
        }

        with pytest.raises(ValueError, match="Only absolute paths are allowed"):
            upload_tools.process_file_input(file_obj, 0)

    def test_process_file_input_nonexistent_path(self):
        """Test error when path doesn't exist."""
        file_obj = {
            "filename": "test.pdf",
            "path": "/nonexistent/path/to/file.pdf"
        }

        with pytest.raises(ValueError, match="path does not exist"):
            upload_tools.process_file_input(file_obj, 0)

    def test_process_file_input_directory_path_rejected(self, tmp_path):
        """Test that directory paths are rejected."""
        file_obj = {
            "filename": "test.pdf",
            "path": str(tmp_path)  # Directory, not file
        }

        with pytest.raises(ValueError, match="path is not a file"):
            upload_tools.process_file_input(file_obj, 0)

    def test_process_file_input_empty_base64(self):
        """Test error when base64 content is empty."""
        file_obj = {
            "filename": "test.pdf",
            "content_base64": "   "  # Empty/whitespace
        }

        with pytest.raises(ValueError, match="empty content_base64"):
            upload_tools.process_file_input(file_obj, 0)

    @pytest.mark.asyncio
    async def test_create_session_with_path_format(self, test_settings, temp_pdf_file):
        """Test creating session with path-based file input."""
        files = [
            {
                "filename": "test.pdf",
                "path": str(temp_pdf_file)
            }
        ]

        result = await upload_tools.create_session_from_uploads(
            project_name="Path Test Project",
            files=files
        )

        try:
            assert result["success"] is True
            assert result["files_saved"] == ["test.pdf"]
            assert result["documents_found"] == 1

        finally:
            await session_tools.delete_session(result["session_id"])

    @pytest.mark.asyncio
    async def test_create_session_mixed_formats(self, test_settings, temp_pdf_file, sample_pdf2_base64):
        """Test creating session with mix of path and base64 files."""
        files = [
            {
                "filename": "path_file.pdf",
                "path": str(temp_pdf_file)
            },
            {
                "filename": "base64_file.pdf",
                "content_base64": sample_pdf2_base64
            }
        ]

        result = await upload_tools.create_session_from_uploads(
            project_name="Mixed Format Project",
            files=files
        )

        try:
            assert result["success"] is True
            assert result["files_saved"] == ["path_file.pdf", "base64_file.pdf"]
            assert result["documents_found"] == 2

        finally:
            await session_tools.delete_session(result["session_id"])

    @pytest.mark.asyncio
    async def test_upload_additional_files_path_format(self, test_settings, temp_pdf_file, temp_pdf_file2, sample_pdf_base64):
        """Test uploading additional files using path format."""
        # Create initial session with base64
        initial_result = await upload_tools.create_session_from_uploads(
            project_name="Additional Files Test",
            files=[{"filename": "initial.pdf", "content_base64": sample_pdf_base64}]
        )

        session_id = initial_result["session_id"]

        try:
            # Add files using path format
            additional_result = await upload_tools.upload_additional_files(
                session_id=session_id,
                files=[
                    {"filename": "additional1.pdf", "path": str(temp_pdf_file2)}
                ]
            )

            assert additional_result["success"] is True
            assert "additional1.pdf" in additional_result["files_added"]
            assert additional_result["documents_found"] == 2

        finally:
            await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_start_review_with_path_format(self, test_settings, temp_pdf_file, temp_pdf_file2):
        """Test complete workflow with path-based uploads."""
        files = [
            {"name": "ProjectPlan.pdf", "path": str(temp_pdf_file)},
            {"name": "Baseline.pdf", "path": str(temp_pdf_file2)}
        ]

        result = await upload_tools.start_review_from_uploads(
            project_name="Full Workflow Path Test",
            files=files,
            auto_extract=False  # Skip evidence extraction for speed
        )

        session_result = result["session_creation"]
        session_id = session_result["session_id"]

        try:
            assert session_result["success"] is True
            assert session_result["documents_found"] == 2

        finally:
            await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_path_deduplication_works(self, test_settings, temp_pdf_file):
        """Test that deduplication works with path-based uploads."""
        # Same file uploaded twice via path
        files = [
            {"filename": "file1.pdf", "path": str(temp_pdf_file)},
            {"filename": "file2.pdf", "path": str(temp_pdf_file)}  # Same file, different name
        ]

        result = await upload_tools.create_session_from_uploads(
            project_name="Path Deduplication Test",
            files=files,
            deduplicate=True
        )

        try:
            # Should detect content duplication
            assert result["deduplication"]["total_duplicates_removed"] == 1
            assert len(result["files_saved"]) == 1

        finally:
            await session_tools.delete_session(result["session_id"])

    def test_process_file_input_path_without_filename(self, temp_pdf_file):
        """Test that filename is extracted from path when not provided (ElizaOS compatibility)."""
        file_obj = {
            "path": str(temp_pdf_file)
            # No 'filename' or 'name' field
        }

        result = upload_tools.process_file_input(file_obj, 0)

        assert result["filename"] == temp_pdf_file.name
        assert "content_base64" in result

    def test_process_file_input_explicit_filename_takes_precedence(self, temp_pdf_file):
        """Test that explicit filename takes precedence over path extraction."""
        file_obj = {
            "filename": "custom_name.pdf",
            "path": str(temp_pdf_file)  # Has different name
        }

        result = upload_tools.process_file_input(file_obj, 0)

        # Should use explicit filename, not extracted from path
        assert result["filename"] == "custom_name.pdf"
        assert result["filename"] != temp_pdf_file.name

    @pytest.mark.asyncio
    async def test_create_session_path_only_format(self, test_settings, temp_pdf_file):
        """Test creating session with path-only format (no filename field)."""
        files = [
            {
                "path": str(temp_pdf_file)
                # No filename - should extract from path
            }
        ]

        result = await upload_tools.create_session_from_uploads(
            project_name="Path Only Test",
            files=files
        )

        try:
            assert result["success"] is True
            assert temp_pdf_file.name in result["files_saved"]
            assert result["documents_found"] == 1

        finally:
            await session_tools.delete_session(result["session_id"])


class TestPathResolution:
    """Test ElizaOS path resolution functionality."""

    def test_resolve_absolute_path_exists(self, tmp_path, sample_pdf_base64):
        """Test that absolute paths that exist are used as-is."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(base64.b64decode(sample_pdf_base64))

        resolved = upload_tools._resolve_file_path(str(test_file))
        assert resolved == test_file
        assert resolved.exists()

    def test_resolve_eliza_media_url_cwd(self, tmp_path, sample_pdf_base64):
        """Test resolving ElizaOS /media/uploads/ URL from current directory."""
        # Create mock ElizaOS structure in temp directory
        eliza_root = tmp_path / "eliza"
        uploads_dir = eliza_root / "packages/cli/.eliza/data/uploads/agents/abc123"
        uploads_dir.mkdir(parents=True)

        test_file = uploads_dir / "test.pdf"
        test_file.write_bytes(base64.b64decode(sample_pdf_base64))

        # Save current directory and change to eliza_root
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(eliza_root)

            # Try to resolve ElizaOS URL
            url_path = "/media/uploads/agents/abc123/test.pdf"
            resolved = upload_tools._resolve_file_path(url_path)

            assert resolved.exists()
            assert resolved == test_file

        finally:
            os.chdir(original_cwd)

    def test_resolve_eliza_media_url_env_var(self, tmp_path, sample_pdf_base64, monkeypatch):
        """Test resolving ElizaOS URL using ELIZA_ROOT environment variable."""
        # Create mock ElizaOS structure
        eliza_root = tmp_path / "eliza"
        uploads_dir = eliza_root / "packages/cli/.eliza/data/uploads/agents/abc123"
        uploads_dir.mkdir(parents=True)

        test_file = uploads_dir / "test.pdf"
        test_file.write_bytes(base64.b64decode(sample_pdf_base64))

        # Set ELIZA_ROOT environment variable
        monkeypatch.setenv('ELIZA_ROOT', str(eliza_root))

        # Try to resolve ElizaOS URL
        url_path = "/media/uploads/agents/abc123/test.pdf"
        resolved = upload_tools._resolve_file_path(url_path)

        assert resolved.exists()
        assert resolved == test_file

    def test_resolve_eliza_media_url_alternative_structure(self, tmp_path, sample_pdf_base64, monkeypatch):
        """Test resolving ElizaOS URL with alternative directory structure (no packages/cli)."""
        # Create alternative structure: .eliza/data/ directly under root
        eliza_root = tmp_path / "eliza"
        uploads_dir = eliza_root / ".eliza/data/uploads/agents/abc123"
        uploads_dir.mkdir(parents=True)

        test_file = uploads_dir / "test.pdf"
        test_file.write_bytes(base64.b64decode(sample_pdf_base64))

        monkeypatch.setenv('ELIZA_ROOT', str(eliza_root))

        url_path = "/media/uploads/agents/abc123/test.pdf"
        resolved = upload_tools._resolve_file_path(url_path)

        assert resolved.exists()
        assert resolved == test_file

    def test_resolve_nonexistent_path_returns_original(self):
        """Test that nonexistent paths are returned as-is (will fail later validation)."""
        fake_path = "/nonexistent/path/to/file.pdf"
        resolved = upload_tools._resolve_file_path(fake_path)

        # Should return original path (Path object)
        assert str(resolved) == fake_path
        assert not resolved.exists()

    def test_resolve_relative_path_from_cwd(self, tmp_path, sample_pdf_base64):
        """Test resolving relative path from current working directory."""
        # Create file in temp directory
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(base64.b64decode(sample_pdf_base64))

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Relative path should resolve from cwd
            resolved = upload_tools._resolve_file_path("test.pdf")

            assert resolved.exists()
            assert resolved == test_file

        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_create_session_with_eliza_url_path(self, tmp_path, test_settings, sample_pdf_base64, monkeypatch):
        """Test creating session with ElizaOS /media/uploads/ URL path."""
        # Create mock ElizaOS structure
        eliza_root = tmp_path / "eliza"
        uploads_dir = eliza_root / "packages/cli/.eliza/data/uploads/agents/abc123"
        uploads_dir.mkdir(parents=True)

        test_file = uploads_dir / "ProjectPlan.pdf"
        test_file.write_bytes(base64.b64decode(sample_pdf_base64))

        # Set ELIZA_ROOT environment variable
        monkeypatch.setenv('ELIZA_ROOT', str(eliza_root))

        # Use ElizaOS URL format
        files = [
            {
                "path": "/media/uploads/agents/abc123/ProjectPlan.pdf"
            }
        ]

        result = await upload_tools.create_session_from_uploads(
            project_name="ElizaOS URL Test",
            files=files
        )

        try:
            assert result["success"] is True
            assert "ProjectPlan.pdf" in result["files_saved"]
            assert result["documents_found"] == 1

        finally:
            await session_tools.delete_session(result["session_id"])
