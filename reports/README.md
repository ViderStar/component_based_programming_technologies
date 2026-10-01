# Reports

Title data: BSUIR, FCSN, POIT, PI; MSc year 2 Artsem Lebiadzevich; supervisor Oleg German (ITAS); Minsk 2026.

| Lab | File |
| --- | --- |
| Lab 1 serialization | [lab1_report.md](lab1_report.md) |
| Lab 2 COM server | [lab2_report.md](lab2_report.md) |
| Lab 1 extra: XML-RPC | [lab1_extra_rpc_report.md](lab1_extra_rpc_report.md) |
| Lab 1 extra: wxPython | [lab1_extra_wxui_report.md](lab1_extra_wxui_report.md) |
| Lab 1 extra: reflection | [lab1_extra_reflection_report.md](lab1_extra_reflection_report.md) |

PDF reports (LaTeX, built with tectonic):

| Lab | PDF | Source |
| --- | --- | --- |
| Lab 1 serialization + extras | [lab1/lab1_report.pdf](lab1/lab1_report.pdf) | [lab1/lab1_report.tex](lab1/lab1_report.tex) |
| Lab 2 COM server, Windows vs Linux vs macOS | [lab2/lab2_report.pdf](lab2/lab2_report.pdf) | [lab2/lab2_report.tex](lab2/lab2_report.tex) |

```bash
cd reports/lab2 && tectonic lab2_report.tex
```

Screenshots in [`screenshots/`](screenshots/) are real window captures made by `python scripts/capture_shots.py` (macOS; needs Screen Recording permission). `lab1_extra_wxui.png` is still a drawn mock from `scripts/render_shots.py`.
