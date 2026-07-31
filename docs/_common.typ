// Shared helpers and generated build metadata for the documentation parts.

#import "build/meta.typ": build_date, commit, version

#let api_signatures = json("build/api.json")

// Show the Python source of an example file.
#let source(path) = raw(read(path), block: true, lang: "python")

// A small "Source / Result" label.
#let tag(label) = {
  v(0.7em)
  text(size: 8.5pt, fill: luma(110), weight: "bold", tracking: 0.6pt)[#label]
}

// The shared treatment for tables authored as part of the documentation prose.
// Generated tytable examples keep their own themes so they demonstrate package output faithfully.
#let docs-table(columns: auto, align: left, ..cells) = table(
  columns: columns,
  align: align,
  inset: 6pt,
  fill: (x, y) => if y == 0 { rgb("#eef5f6") } else { none },
  stroke: (x, y) => (
    top: if y == 0 { 0.5pt + rgb("#087e8b") } else { none },
    bottom: if y == 0 { 0.5pt + rgb("#087e8b") } else { 0.35pt + rgb("#dfe6e2") },
    left: if x == 0 { 0.5pt + rgb("#087e8b") } else { 0.45pt + rgb("#91c4ca") },
    right: if x == columns.len() - 1 { 0.5pt + rgb("#087e8b") } else { 0.45pt + rgb("#91c4ca") },
  ),
  ..cells,
  table.hline(stroke: 0.5pt + rgb("#087e8b")),
)

// A scannable API-reference card: task label followed by a Python signature.
#let api(title, sig) = block(
  width: 100%,
  breakable: false,
  fill: rgb("#eef5f6"),
  inset: (x: 10pt, y: 8pt),
  radius: 5pt,
  spacing: 0.8em,
)[
  #set par(justify: false)
  #text(size: 8.5pt, weight: "bold", fill: rgb("#087e8b"), tracking: 0.4pt)[
    #upper(title)
  ]
  #v(0.35em)
  #raw(sig, block: true, lang: "python")
]
