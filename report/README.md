# IEEE report

Compile main.tex using pdfLaTeX and BibTeX:

```powershell
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Replace the author and institution placeholders in main.tex. This report follows
the reference's section order, adapted to our implementation. The reference's
Fuseki section and website appendix are replaced by our CLI and usage commands.
No deployed interface or remote query results are claimed.

## What is evaluation.json?

This is an optional record created while preparing the earlier report. It is not
used by the application, and LaTeX does not read it. It was produced on 2026-10-08
by an ad hoc Python evaluation (not an existing pipeline script):

1. Parse movies.ttl and ontology.owl using RDFLib; count triples and class instances.
2. Execute queries 1-9, 11, 12 and find_movie on the movie graph.
3. Read the candidate CSVs and count statuses and approved local entities; parse
   the three link files and count their triples.
4. Apply owlrl.DeductiveClosure(OWLRL_Semantics) to movies plus ontology; rerun 11/12.
5. Combine data, ontology and all links, apply reasoning, and run the missing-name
   and disjoint-type queries.

No live external lookup was run for these measurements. The simplified report
uses only a few of these results; it does not need this JSON file. It remains
here as a record of how the reported numbers were obtained. Counts change if
the source files, queries, or library behavior change.

Source checks do not replace compilation: inspect the PDF layout in your TeX setup.

The report includes two TikZ diagrams (workflow and reasoning), a CSV-to-RDF
mapping table, and a before/after inference table. TikZ uses the arrows.meta
and positioning libraries; no external image files are required.

The bibliography is limited to three sources already present in the reference
project: Linked Data, RDF 1.1 Concepts, and SPARQL 1.1 Query Language.
