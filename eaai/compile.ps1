# Compile the complete manuscript, anonymized review file, and title page.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Build-Tex($name) {
    pdflatex -interaction=nonstopmode "$name.tex"
    if (Test-Path "$name.aux") {
        bibtex $name
        pdflatex -interaction=nonstopmode "$name.tex"
        pdflatex -interaction=nonstopmode "$name.tex"
    }
}

Build-Tex manuscript
Build-Tex manuscript_anonymous
pdflatex -interaction=nonstopmode title_page.tex
pdflatex -interaction=nonstopmode title_page.tex

Write-Host "Done: manuscript.pdf, manuscript_anonymous.pdf, title_page.pdf"
