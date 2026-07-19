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
