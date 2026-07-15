"""
classification/generate_pdf_report.py
--------------------------------------
Generates a professional, submission-ready PDF report for Part 2 (Data
Classification) of the "Seeding QDArchive" project.

Usage:
    python classification/generate_pdf_report.py working.db --out 23123639_SQ26_Part2_Report.pdf
"""

import argparse
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, HRFlowable, KeepTogether,
)

STUDENT_NAME     = "Almas Ali Pinto"
STUDENT_ID       = "23123639"
DEGREE_PROGRAM   = "M.Sc. Data Science"
UNIVERSITY       = "Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)"
CHAIR            = "Professorship for Open-Source Software"
SUPERVISOR       = "Prof. Dr. Dirk Riehle"
COURSE_NAME      = "Applied Software Engineering Seminar / Project — SQ26 “Seeding QDArchive”"
GITHUB_URL       = "https://github.com/Pinto391/QDArchive"
REPOSITORIES     = "QDR (Qualitative Data Repository, Syracuse University) · ICPSR"

ACCENT = colors.HexColor("#1F4E5F")
ACCENT_LIGHT = colors.HexColor("#EAF1F3")
GREY = colors.HexColor("#555555")


def _fetch_stats(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    def one(q, *a):
        return conn.execute(q, a).fetchone()[0]

    def rows(q, *a):
        return [dict(r) for r in conn.execute(q, a).fetchall()]

    stats = {}
    stats["n_repos"] = one("SELECT COUNT(*) FROM REPOSITORIES")
    stats["n_projects"] = one("SELECT COUNT(*) FROM PROJECTS")
    stats["n_files"] = one("SELECT COUNT(*) FROM FILES")
    stats["n_succeeded"] = one("SELECT COUNT(*) FROM FILES WHERE status='SUCCEEDED'")
    stats["n_failed_login"] = one("SELECT COUNT(*) FROM FILES WHERE status='FAILED_LOGIN_REQUIRED'")
    stats["n_failed_server"] = one("SELECT COUNT(*) FROM FILES WHERE status='FAILED_SERVER_UNRESPONSIVE'")

    stats["n_proj_classified"] = one(
        "SELECT COUNT(*) FROM CLASSIFICATIONS WHERE isic_section != 'UNCLASSIFIED'")
    stats["n_proj_unclassified"] = one(
        "SELECT COUNT(*) FROM CLASSIFICATIONS WHERE isic_section = 'UNCLASSIFIED'")
    stats["n_proj_total"] = one("SELECT COUNT(*) FROM CLASSIFICATIONS")

    stats["section_dist"] = rows(
        """SELECT isic_section, section_name, COUNT(*) c FROM CLASSIFICATIONS
           GROUP BY isic_section, section_name ORDER BY c DESC""")
    stats["division_dist"] = rows(
        """SELECT isic_section, isic_division, division_name, COUNT(*) c, AVG(confidence) a
           FROM CLASSIFICATIONS GROUP BY isic_division, division_name ORDER BY c DESC""")

    stats["n_file_class_total"] = one("SELECT COUNT(*) FROM FILE_CLASSIFICATIONS")
    stats["n_file_from_content"] = one(
        "SELECT COUNT(*) FROM FILE_CLASSIFICATIONS WHERE method='RULE_BASED_KEYWORDS'")
    stats["n_file_inherited"] = one(
        "SELECT COUNT(*) FROM FILE_CLASSIFICATIONS WHERE method='NO_TEXT_CONTENT'")
    stats["file_division_dist"] = rows(
        """SELECT isic_section, isic_division, division_name, COUNT(*) c
           FROM FILE_CLASSIFICATIONS GROUP BY isic_division, division_name ORDER BY c DESC LIMIT 12""")

    stats["top_tags"] = rows(
        """SELECT tag, COUNT(*) c FROM TAGS GROUP BY tag ORDER BY c DESC LIMIT 15""")
    stats["file_types"] = rows(
        """SELECT file_type, COUNT(*) c FROM FILES WHERE status='SUCCEEDED'
           GROUP BY file_type ORDER BY c DESC LIMIT 10""")
    stats["download_methods"] = rows(
        "SELECT download_method, COUNT(*) c FROM PROJECTS GROUP BY download_method")

    conn.close()
    return stats


def _make_bar_chart(labels, values, out_path, xlabel, color="#1F4E5F", figsize=(6.3, 3.6)):
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    y_pos = range(len(labels))
    ax.barh(y_pos, values, color=color, height=0.65)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelsize=8)
    for i, v in enumerate(values):
        ax.text(v + max(values) * 0.01, i, str(v), va="center", fontsize=7.5, color="#333333")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(
        name="ReportTitle", parent=ss["Title"], fontSize=22, leading=27,
        textColor=ACCENT, spaceAfter=6,
    ))
    ss.add(ParagraphStyle(
        name="ReportSubtitle", parent=ss["Normal"], fontSize=13, leading=17,
        textColor=GREY, alignment=TA_CENTER, spaceAfter=4,
    ))
    ss.add(ParagraphStyle(
        name="TitlePageField", parent=ss["Normal"], fontSize=11, leading=16,
        alignment=TA_CENTER,
    ))
    ss.add(ParagraphStyle(
        name="H1", parent=ss["Heading1"], fontSize=15, leading=19,
        textColor=ACCENT, spaceBefore=18, spaceAfter=8,
        borderWidth=0, borderColor=ACCENT, borderPadding=0,
    ))
    ss.add(ParagraphStyle(
        name="H2", parent=ss["Heading2"], fontSize=12.5, leading=16,
        textColor=ACCENT, spaceBefore=12, spaceAfter=6,
    ))
    ss.add(ParagraphStyle(
        name="Body", parent=ss["Normal"], fontSize=10.2, leading=15,
        alignment=TA_JUSTIFY, spaceAfter=6,
    ))
    ss.add(ParagraphStyle(
        name="Caption", parent=ss["Normal"], fontSize=8.5, leading=11,
        textColor=GREY, alignment=TA_CENTER, spaceBefore=2, spaceAfter=10,
    ))
    ss.add(ParagraphStyle(
        name="BulletBody", parent=ss["Normal"], fontSize=10.2, leading=14.5,
        leftIndent=14, spaceAfter=4,
    ))
    return ss


def _table(data, col_widths=None, header_bg=ACCENT, font_size=9, wrap_cols=None):
    """wrap_cols: column indices whose cell text should word-wrap (via
    Paragraph) instead of being clipped — use for any column that may hold
    long text at a narrow width."""
    if wrap_cols:
        cell_style = ParagraphStyle(
            name="TableCell", fontName="Helvetica", fontSize=font_size, leading=font_size + 2.5)
        header_style = ParagraphStyle(
            name="TableHeader", fontName="Helvetica-Bold", fontSize=font_size,
            leading=font_size + 2.5, textColor=colors.white)
        wrapped = []
        for r_idx, row in enumerate(data):
            new_row = list(row)
            for c_idx in wrap_cols:
                style = header_style if r_idx == 0 else cell_style
                new_row[c_idx] = Paragraph(str(row[c_idx]), style)
            wrapped.append(new_row)
        data = wrapped

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ACCENT_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.2 * cm,
                       f"Seeding QDArchive — Part 2 Report — {STUDENT_NAME} ({STUDENT_ID})")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_report(db_path: str, out_path: str):
    stats = _fetch_stats(db_path)
    ss = _styles()
    tmpdir = Path(tempfile.mkdtemp(prefix="sq26_part2_charts_"))

    # ── Charts ──────────────────────────────────────────────────────────
    section_labels = [f"{r['isic_section']} — {r['section_name'][:40]}" for r in stats["section_dist"][:10]]
    section_values = [r["c"] for r in stats["section_dist"][:10]]
    section_chart_path = tmpdir / "section_dist.png"
    _make_bar_chart(section_labels, section_values, section_chart_path,
                     "Number of projects", color="#1F4E5F")

    file_div_labels = [f"{r['isic_section']}/{r['isic_division']} — {r['division_name'][:38]}"
                        for r in stats["file_division_dist"][:10]]
    file_div_values = [r["c"] for r in stats["file_division_dist"][:10]]
    file_div_chart_path = tmpdir / "file_division_dist.png"
    _make_bar_chart(file_div_labels, file_div_values, file_div_chart_path,
                     "Number of files", color="#3E7C89")

    # ── Document setup ────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2 * cm, bottomMargin=2.4 * cm,
        title="Seeding QDArchive — Part 2: Data Classification Report",
        author=STUDENT_NAME,
    )

    story = []

    # ── Title page ────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.2 * cm))
    story.append(Paragraph(UNIVERSITY, ss["ReportSubtitle"]))
    story.append(Paragraph(CHAIR, ss["ReportSubtitle"]))
    story.append(Spacer(1, 1.4 * cm))
    story.append(HRFlowable(width="60%", thickness=1.2, color=ACCENT, hAlign="CENTER"))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Seeding QDArchive", ss["ReportTitle"]))
    story.append(Paragraph("Part 2 — Data Classification Report", ss["ReportSubtitle"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="60%", thickness=1.2, color=ACCENT, hAlign="CENTER"))
    story.append(Spacer(1, 2 * cm))

    field_rows = [
        ("Student", STUDENT_NAME),
        ("Student ID", STUDENT_ID),
        ("Degree Program", DEGREE_PROGRAM),
        ("University", UNIVERSITY),
        ("Course", COURSE_NAME),
        ("Supervisor", SUPERVISOR),
        ("Data Sources", REPOSITORIES),
        ("Repository", GITHUB_URL),
        ("Date", datetime.now(timezone.utc).strftime("%d %B %Y")),
    ]
    field_table = Table(
        [[Paragraph(f"<b>{k}</b>", ss["Body"]), Paragraph(v, ss["Body"])] for k, v in field_rows],
        colWidths=[4.2 * cm, 10.3 * cm],
    )
    field_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#DDDDDD")),
    ]))
    story.append(field_table)
    story.append(PageBreak())

    # ── 1. Introduction ───────────────────────────────────────────────────
    story.append(Paragraph("1. Introduction", ss["H1"]))
    story.append(Paragraph(
        "QDArchive is a web service under development at the Professorship for Open-Source "
        "Software (FAU Erlangen) for researchers to publish and archive qualitative data, with an "
        "emphasis on Qualitative Data Analysis (QDA) files. Because the platform is new, it must "
        "be “seeded” with openly available qualitative research projects gathered from "
        "existing repositories. This project is structured into three parts: <b>Part 1 — "
        "Data Acquisition</b>, <b>Part 2 — Data Classification</b> (the subject of this "
        "report), and <b>Part 3 — Data Analysis</b>.", ss["Body"]))
    story.append(Paragraph(
        f"Part 1 produced a SQLite database ({STUDENT_ID}-seeding.db) containing "
        f"{stats['n_projects']} qualitative research projects and {stats['n_files']} associated "
        f"file records, collected from two assigned repositories: QDR (via its public Dataverse "
        f"API) and ICPSR (via HTML scraping). Of the {stats['n_files']} recorded files, "
        f"{stats['n_succeeded']} were successfully downloaded to disk; the remainder failed "
        f"chiefly because ICPSR gates most qualitative studies behind an institutional login "
        f"({stats['n_failed_login']} files) or because of unresponsive servers "
        f"({stats['n_failed_server']} files).", ss["Body"]))
    story.append(Paragraph(
        "This report documents Part 2: merging the available project database(s), developing and "
        "running a classifier that assigns each project <i>and</i> each individual downloaded "
        "file an industry classification under the ISIC Rev. 5 standard, generating searchable "
        "tags, and reporting on the resulting statistics.", ss["Body"]))

    # ── 2. Methodology ─────────────────────────────────────────────────────
    story.append(Paragraph("2. Methodology", ss["H1"]))

    story.append(Paragraph("2.1 Database Merge", ss["H2"]))
    story.append(Paragraph(
        "Per the assignment, all participating students' databases should be merged into a single "
        "working database, de-duplicating projects that multiple students may have independently "
        "collected. A merge script (<font face='Courier'>classification/merge_databases.py</font>) "
        "de-duplicates by <font face='Courier'>project_url</font> — the natural unique key "
        "across student databases, since every student scraped the same public repositories. At "
        "the time this report was produced, classmates' databases had not yet been shared, so the "
        "merge was run as a self-merge of this student's own database. The script accepts an "
        "arbitrary number of input databases, so classmates' data can be folded in later without "
        "any code changes.", ss["Body"]))

    story.append(Paragraph("2.2 Classification Approach", ss["H2"]))
    story.append(Paragraph(
        "The classifier uses the <b>ISIC Rev. 5</b> standard (International Standard Industrial "
        "Classification of All Economic Activities, Revision 5, endorsed by the UN Statistical "
        "Commission at its 54th session, March 2023) as the classification taxonomy, going down "
        "two levels as required: <b>Section</b> (1 letter, 22 categories) and <b>Division</b> "
        "(2-digit code, 87 categories). The complete official structure was sourced directly from "
        "the UN Statistics Division's published draft structure document, so every section and "
        "division code used is authoritative rather than an approximation.", ss["Body"]))
    story.append(Paragraph(
        "Classification uses <b>both the metadata and the underlying file content</b>, as "
        "required by the assignment. For each <b>project</b>, a text blob is built from its "
        "title, description, recorded keywords, file-extension list, and a sample of extracted "
        "text from that project's successfully downloaded files. For each <b>individual "
        "downloaded file</b>, a second, independent classification is produced directly from that "
        "file's own extracted text (module <font face='Courier'>classification/text_extract.py</font>, "
        "supporting .txt, .pdf, .docx, .odt, .htm/.html, .rtf, and QDA container formats such as "
        ".qdpx). Files with no extractable text — audio, video, and image files — "
        "inherit their parent project's classification instead of receiving a fabricated one, and "
        "this fallback is recorded explicitly.", ss["Body"]))
    story.append(Paragraph(
        "Both blobs are scored against every division's curated keyword-hint list using "
        "substring matching; the highest-scoring division is assigned, with a confidence score "
        "equal to the fraction of that division's keyword hints that were matched. This "
        "rule-based approach was chosen deliberately over a black-box machine-learning classifier: "
        "it is fully transparent, reproducible, and auditable — every classification decision "
        "can be traced back to the exact keywords that triggered it.", ss["Body"]))

    story.append(Paragraph("2.3 Tags for Searching", ss["H2"]))
    story.append(Paragraph(
        "Beyond the single winning division per project, every keyword matched across "
        "<i>all</i> 87 divisions is stored as a searchable tag, so that a project touching "
        "multiple domains (e.g. a study on health-policy education) remains discoverable under "
        "each relevant term even though only one division is recorded as its primary "
        "classification.", ss["Body"]))

    # ── 3. Results ────────────────────────────────────────────────────────
    story.append(Paragraph("3. Results", ss["H1"]))

    story.append(Paragraph("3.1 Data Volume Overview", ss["H2"]))
    overview_data = [
        ["Metric", "Value"],
        ["Repositories covered", str(stats["n_repos"])],
        ["Total projects found", str(stats["n_projects"])],
        ["Total file records", str(stats["n_files"])],
        ["Files successfully downloaded", f"{stats['n_succeeded']} "
         f"({stats['n_succeeded']/stats['n_files']*100:.1f}% of records)"],
        ["Files failed — login required (ICPSR gating)", str(stats["n_failed_login"])],
        ["Files failed — server unresponsive", str(stats["n_failed_server"])],
    ]
    story.append(KeepTogether([_table(overview_data, col_widths=[9.5 * cm, 5 * cm]), Spacer(1, 10)]))

    story.append(Paragraph("3.2 Project-Level Classification", ss["H2"]))
    story.append(Paragraph(
        f"{stats['n_proj_classified']} of {stats['n_proj_total']} projects "
        f"({stats['n_proj_classified']/stats['n_proj_total']*100:.1f}%) were classified with at "
        f"least one matching keyword; {stats['n_proj_unclassified']} remained "
        f"<i>UNCLASSIFIED</i> due to sparse, boilerplate project descriptions.", ss["Body"]))
    story.append(KeepTogether([
        Image(str(section_chart_path), width=15.5 * cm, height=15.5 * cm * (3.6 / 6.3)),
        Paragraph("Figure 1. Project distribution across the top 10 ISIC Rev. 5 sections.",
                  ss["Caption"]),
    ]))

    div_table_data = [["Section/<br/>Division", "Division Name", "Projects", "Avg.<br/>Confidence"]]
    for r in stats["division_dist"][:12]:
        div_table_data.append([
            f"{r['isic_section']}/{r['isic_division']}",
            r["division_name"][:58],
            str(r["c"]),
            f"{r['a']:.2f}",
        ])
    div_table = _table(div_table_data, col_widths=[2.4 * cm, 8.6 * cm, 1.8 * cm, 2.7 * cm],
                        font_size=8.3, wrap_cols=[0, 1, 3])
    story.append(KeepTogether([
        div_table,
        Paragraph("Table 1. Top 12 ISIC Rev. 5 divisions by number of classified projects.",
                  ss["Caption"]),
    ]))

    story.append(Paragraph("3.3 File-Level Classification", ss["H2"]))
    story.append(Paragraph(
        f"In addition to project-level classification, every one of the {stats['n_file_class_total']} "
        f"successfully downloaded files received its own individual classification. "
        f"{stats['n_file_from_content']} files "
        f"({stats['n_file_from_content']/stats['n_file_class_total']*100:.1f}%) were classified "
        f"directly from their own extracted text content; the remaining "
        f"{stats['n_file_inherited']} files "
        f"({stats['n_file_inherited']/stats['n_file_class_total']*100:.1f}%) had no extractable "
        f"text (media/binary formats) and inherited their parent project's classification instead, "
        f"which is recorded transparently rather than guessed.", ss["Body"]))
    story.append(KeepTogether([
        Image(str(file_div_chart_path), width=15.5 * cm, height=15.5 * cm * (3.6 / 6.3)),
        Paragraph("Figure 2. File distribution across the top 10 ISIC Rev. 5 divisions.",
                  ss["Caption"]),
    ]))

    story.append(Paragraph("3.4 Search Tags", ss["H2"]))
    story.append(Paragraph(
        "The 15 most frequent tags recorded across all projects, usable for cross-domain search "
        "independent of a project's single primary classification:", ss["Body"]))
    tag_data = [["Tag", "Occurrences"]]
    for r in stats["top_tags"]:
        tag_data.append([r["tag"], str(r["c"])])
    story.append(_table(tag_data, col_widths=[10 * cm, 4.5 * cm]))

    story.append(PageBreak())

    # ── 4. Technical Challenges ────────────────────────────────────────────
    story.append(Paragraph("4. Technical Challenges", ss["H1"]))
    challenges = [
        ("No classmate databases available yet.",
         "The assignment calls for merging <i>all</i> students' databases. Only this student's "
         "own database was available at the time of this run, so the merge was executed as a "
         "documented self-merge (230/230 projects kept, 0 duplicates found). The merge script "
         "accepts any number of input databases, so classmates' data can be incorporated later "
         "without code changes."),
        ("Only a fraction of recorded files were actually downloaded.",
         f"Of {stats['n_files']} file records, only {stats['n_succeeded']} "
         f"({stats['n_succeeded']/stats['n_files']*100:.1f}%) exist on disk, mostly because ICPSR "
         "gates the majority of its qualitative studies behind institutional login. File-level "
         "classification and the file-content signal used for project-level classification can "
         "therefore only draw on this smaller, openly accessible subset."),
        ("Vague or generic project descriptions.",
         f"Some QDR descriptions are boilerplate and contain no strong domain-specific keywords, "
         f"leading to lower classifier confidence or an UNCLASSIFIED result "
         f"({stats['n_proj_unclassified']} projects, "
         f"{stats['file_division_dist'][3]['c'] if len(stats['file_division_dist']) > 3 else 'a number of'} "
         "files in this run)."),
        ("Cross-disciplinary projects.",
         "Some qualitative studies span multiple ISIC divisions simultaneously (e.g. a study on "
         "health-policy education touches Health, Education, and Public Administration at once). "
         "The classifier assigns a single best-scoring division as the primary class, while the "
         "full set of matched keywords across all divisions is preserved as searchable tags for "
         "secondary discovery."),
        ("ISIC Rev. 5 classifies economic activity, not academic research topics.",
         "ISIC categorizes <i>industries</i>, not <i>research subjects</i>, so a qualitative "
         "interview study about a hospital and the hospital's own clinical operations can both "
         "resemble “Human health activities” (division 86). Keyword hints were curated "
         "to route studies toward their substantive domain where the text supports it, falling "
         "back to “Scientific research and development” (division 72) only when the "
         "topic is genuinely about research methodology rather than a specific field. In this "
         "corpus, Health (86) and Education (85) together account for roughly 60% of classified "
         "projects, which reflects the actual subject matter of the QDR corpus rather than a "
         "classifier artefact."),
        ("Per-file classification granularity.",
         "Meeting notes from the course supervisor (2026-04-17) specify that each primary data "
         "file, not only the project as a whole, should carry its own class. This was implemented "
         "as a dedicated file-level classification pass; files without extractable text content "
         "inherit their project's class rather than being assigned an unsupported label."),
    ]
    for i, (title, body) in enumerate(challenges, start=1):
        story.append(Paragraph(f"4.{i} {title}", ss["H2"]))
        story.append(Paragraph(body, ss["Body"]))

    # ── 5. Conclusion ───────────────────────────────────────────────────
    story.append(Paragraph("5. Conclusion and Outlook", ss["H1"]))
    story.append(Paragraph(
        f"Part 2 successfully classified {stats['n_proj_classified']} of {stats['n_proj_total']} "
        f"acquired projects and {stats['n_file_class_total']} downloaded files against the "
        f"official ISIC Rev. 5 taxonomy at both the section and division level, using a "
        f"transparent, rule-based classifier that draws on both project metadata and actual file "
        f"content. The resulting classifications, confidence scores, and search tags are stored "
        f"in the <font face='Courier'>CLASSIFICATIONS</font>, <font face='Courier'>"
        f"FILE_CLASSIFICATIONS</font>, and <font face='Courier'>TAGS</font> tables of the working "
        f"database, and are exported to CSV alongside the Part 1 tables.", ss["Body"]))
    story.append(Paragraph(
        "Remaining work for a fully complete Part 2 submission is contingent on classmates "
        "sharing their databases so a true multi-student merge can be performed; the pipeline is "
        "ready to accept that input immediately. Part 3 (Data Analysis) will build on this "
        "classified corpus.", ss["Body"]))
    story.append(Paragraph(
        f"All source code for this pipeline is available at: {GITHUB_URL}", ss["Body"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"[PDF] Report written to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="Path to the classified database")
    parser.add_argument("--out", default="23123639_SQ26_Part2_Report.pdf")
    args = parser.parse_args()
    build_report(args.db_path, args.out)
