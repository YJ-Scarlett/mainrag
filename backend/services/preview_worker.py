import shutil
import sys
from pathlib import Path


def convert_to_pdf(source: Path, output: Path) -> None:
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        shutil.copy2(source, output)
        return

    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    application = None
    try:
        if suffix in {".doc", ".docx"}:
            application = win32com.client.DispatchEx("Word.Application")
            application.Visible = False
            application.DisplayAlerts = 0
            document = application.Documents.Open(str(source.resolve()), ReadOnly=True)
            try:
                document.ExportAsFixedFormat(str(output.resolve()), 17)
            finally:
                document.Close(False)
        elif suffix in {".ppt", ".pptx"}:
            application = win32com.client.DispatchEx("PowerPoint.Application")
            presentation = application.Presentations.Open(
                str(source.resolve()),
                ReadOnly=True,
                Untitled=False,
                WithWindow=False,
            )
            try:
                presentation.SaveAs(str(output.resolve()), 32)  # ppSaveAsPDF
            finally:
                presentation.Close()
        else:
            raise RuntimeError("unsupported preview type")
    finally:
        if application is not None:
            application.Quit()
        pythoncom.CoUninitialize()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python -m services.preview_worker <source> <output>", file=sys.stderr)
        return 2
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    convert_to_pdf(source, output)
    if not output.exists():
        print("preview pdf was not created", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
