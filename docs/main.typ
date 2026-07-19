// tytable documentation
// Build:  make docs   (runs build_examples.py then typst compile)

#set page(
  paper: "a4",
  margin: (x: 2.4cm, y: 2.5cm),
  numbering: "1",
  number-align: center,
)

#set text(font: "New Computer Modern", size: 10.5pt, lang: "en")
#set par(justify: true, leading: 0.8em)

#let docs-heading-numbering(..numbers) = {
  let values = numbers.pos()
  if values.len() == 1 {
    [Part #numbering("I", ..values)]
  } else {
    numbering("1.1", ..values)
  }
}

#set heading(numbering: docs-heading-numbering)

// Code blocks: light panel, mono font.
#show raw: set text(font: "DejaVu Sans Mono")
#show raw.where(block: true): it => block(
  fill: luma(246),
  inset: 9pt,
  radius: 5pt,
  width: 100%,
  it,
)

// Center every tytable figure and keep it from breaking awkwardly.
#show figure.where(kind: "tytable"): set align(center)

#import "_common.typ": build_date, commit, version

// ---------------------------------------------------------------------------
// Title page
// ---------------------------------------------------------------------------

#set page(numbering: none)

#align(center + horizon)[
  #block(height: 3cm)[]
  #text(size: 34pt, weight: "bold")[tytable]
  #v(0.4em)
  #text(size: 13pt, fill: luma(90))[Typst tables from Polars DataFrames]
  #v(2.2cm)
  #line(length: 32%, stroke: 0.6pt + luma(70))
  #v(0.6cm)
  #text(size: 11pt)[Documentation]
  #v(0.4cm)
  #text(size: 10pt, fill: luma(110))[Version #version]
  #v(0.25cm)
  #text(size: 9pt, fill: luma(140), tracking: 0.4pt)[#commit · built #build_date]
]

#pagebreak()

// ---------------------------------------------------------------------------
// Table of contents
// ---------------------------------------------------------------------------

#set page(numbering: none)

#align(center)[
  #text(size: 18pt, weight: "bold")[Contents]
]
#v(0.8em)
#set text(size: 9pt)
#columns(2, gutter: 1.2cm)[
  #outline(title: none, indent: 1.2em, depth: 3)
]

#pagebreak()

// ---------------------------------------------------------------------------
// Body
// ---------------------------------------------------------------------------

#set page(numbering: "1")
#counter(page).update(1)
#set text(size: 10.5pt)

#include "tutorial.typ"
#include "guides.typ"
#include "reference.typ"
