"""Tests for main module."""

from app.main import main


def test_main(capsys) -> None:
    """Test main function output."""
    main()
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out
