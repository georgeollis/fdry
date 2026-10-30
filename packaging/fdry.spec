"""Build a standalone console executable on the target operating system."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

root = Path(SPECPATH).parent
datas = [(str(root / "LICENSE"), ".")]
binaries = []
hiddenimports = []

# Generated SDKs and OpenAI load operation/model modules dynamically.
for package in (
    "azure.ai.projects",
    "azure.mgmt.cognitiveservices",
    "azure.identity",
    "openai",
):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports

datas += copy_metadata("fdry")

analysis = Analysis(
    [str(root / "src" / "fdry" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="fdry",
    console=True,
    upx=False,
)
