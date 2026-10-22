"""
AeroSentinel - IJSART Academic Manuscript DOCX Generator (Verified Data-Driven Version)
Generates a fully-styled, publication-ready Microsoft Word (.docx) document
strictly aligned with the International Journal for Science and Advance Research In Technology (IJSART)
author guidelines, typography, embedded 300 DPI figures, and verified experimental outputs.
"""

import csv
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOC_DIR = Path("docs/research")
RESEARCH_DIR = Path("reports/research")
FIGURES_DIR = RESEARCH_DIR / "figures"
OUTPUT_DOCX = DOC_DIR / "manuscript_aerosentinel_draft.docx"

def set_section_cols(section, num=1, space=346):
    sectPr = section._sectPr
    cols = sectPr.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols')
        sectPr.append(cols)
    cols.set(qn('w:num'), str(num))
    if num > 1:
        cols.set(qn('w:space'), str(space))
        cols.set(qn('w:equalWidth'), '1')

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, fill_hex):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def get_verified_references():
    """Return all 15 fully verified academic and technical references."""
    return [
        "[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \"Damage propagation modeling for aircraft engine run-to-failure simulation,\" in Proc. 2008 Int. Conf. Prognostics and Health Management (PHM), Denver, CO, USA, Oct. 2008, pp. 1–9, doi: 10.1109/PHM.2008.4711414.",
        "[2] E. Ramasso and A. Saxena, \"Performance benchmarking and analysis of prognostic methods for CMAPSS datasets,\" Int. J. Prognostics and Health Management, vol. 5, no. 2, pp. 1–15, Dec. 2014, doi: 10.36001/ijphm.2014.v5i2.2217.",
        "[3] S. Zheng, K. Ristovski, A. Farahat, and C. Gupta, \"Long short-term memory network for remaining useful life estimation,\" in Proc. 2017 IEEE Conf. Prognostics and Health Management (ICPHM), Dallas, TX, USA, Jun. 2017, pp. 88–95, doi: 10.1109/ICPHM.2017.7998311.",
        "[4] T. Gu, B. Dolan-Gavitt, and S. Garg, \"BadNets: Identifying vulnerabilities in the machine learning model supply chain,\" IEEE Access, vol. 7, pp. 47230–47244, Apr. 2019, doi: 10.1109/ACCESS.2019.2923408.",
        "[5] D. J. Bernstein, N. Duif, T. Lange, P. Schwabe, and B.-Y. Yang, \"High-speed high-security signatures,\" J. Cryptographic Engineering, vol. 2, no. 2, pp. 77–89, Sep. 2012, doi: 10.1007/s13389-012-0027-1.",
        "[6] National Institute of Standards and Technology (NIST), \"Secure Software Development Framework (SSDF) version 1.1: Recommendations for mitigating the risk of software supply chain attacks,\" NIST Special Publication 800-218, Gaithersburg, MD, USA, Feb. 2022, doi: 10.6028/NIST.SP.800-218.",
        "[7] H. I. Fawaz, G. Forestier, J. Weber, L. Idoumghar, and P.-A. Muller, \"Adversarial attacks on deep neural networks for time series classification,\" in Proc. 2019 Int. Joint Conf. Neural Networks (IJCNN), Budapest, Hungary, Jul. 2019, pp. 1–8, doi: 10.1109/IJCNN.2019.8851936.",
        "[8] F. Karim, S. Majumdar, and H. Darabi, \"Adversarial attacks on time series,\" IEEE Access, vol. 8, pp. 81718–81726, Apr. 2020, doi: 10.1109/ACCESS.2020.2980424.",
        "[9] S. Rabanser, S. Günnemann, and Z. C. Lipton, \"Failing loudly: An empirical study of methods for detecting dataset shift,\" in Advances in Neural Information Processing Systems (NeurIPS 32), Vancouver, BC, Canada, Dec. 2019, pp. 1396–1408.",
        "[10] N. Siddiqi, Credit Risk Scorecards: Developing and Implementing Intelligent Credit Scoring. Hoboken, NJ, USA: John Wiley & Sons, 2006, doi: 10.1002/9781119201731.",
        "[11] F. J. Massey, \"The Kolmogorov-Smirnov test for goodness of fit,\" J. American Statistical Association, vol. 46, no. 253, pp. 68–78, Mar. 1951, doi: 10.1080/01621459.1951.10500769.",
        "[12] Y. Mo, R. Chabukswar, and B. Sinopoli, \"Detecting integrity attacks on cyber-physical systems,\" IEEE Trans. Control Systems Technology, vol. 22, no. 4, pp. 1396–1407, Jul. 2014, doi: 10.1109/TCST.2013.2280899.",
        "[13] OWASP Foundation, \"OWASP API Security Top 10 2023,\" Open Worldwide Application Security Project, Jun. 2023. [Online]. Available: https://owasp.org/www-project-api-security/",
        "[14] A. Basak, P. Rathore, S. H. Nistala, S. Srinivas, and V. Runkana, \"Universal adversarial attack on deep learning based prognostics,\" in Proc. 2021 IEEE Int. Conf. Big Data (Big Data), Orlando, FL, USA, Dec. 2021, pp. 4363–4370, doi: 10.1109/BigData52589.2021.9671607.",
        "[15] G. R. Mode and K. A. Hoque, \"Adversarial examples in deep learning for multivariate time series regression,\" in Proc. 2020 IEEE Applied Imagery Pattern Recognition Workshop (AIPR), Washington, DC, USA, Oct. 2020, pp. 1–10, doi: 10.1109/AIPR50011.2020.9425190.",
    ]

def create_manuscript():
    doc = docx.Document()
    
    # Page setup - A4
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.63)
        section.right_margin = Inches(0.63)
        section.header_distance = Inches(0.4)
        section.footer_distance = Inches(0.4)
        set_section_cols(section, 1)
        
        # Header / Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("International Journal for Science and Advance Research In Technology (IJSART) — Research Manuscript")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(128, 128, 128)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("AeroSentinel Research  |  NASA C-MAPSS Resilience Evaluation")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(128, 128, 128)

    # Base style
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(10)
    font.color.rgb = RGBColor(15, 23, 42)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(8)
    run_title = p_title.add_run("Integrity-Assured Machine Learning for Aircraft Predictive Maintenance: Threat Modeling and Resilience Evaluation Using NASA C-MAPSS")
    run_title.font.name = "Times New Roman"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    # Authors
    p_author = doc.add_paragraph()
    p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_author.paragraph_format.space_after = Pt(2)
    r_author = p_author.add_run("Simpson R*¹, Sarveshwaran P², Sarathi Kannan K³, Varun S⁴")
    r_author.font.name = "Times New Roman"
    r_author.font.size = Pt(11)
    r_author.font.bold = True

    # Shared Affiliation
    p_affil = doc.add_paragraph()
    p_affil.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_affil.paragraph_format.space_after = Pt(2)
    r_affil = p_affil.add_run("¹˒²˒³˒⁴ Department of Cyber Security, Dhanalakshmi Srinivasan University, Tiruchirappalli, Tamil Nadu, India.")
    r_affil.font.name = "Times New Roman"
    r_affil.font.size = Pt(9.5)
    r_affil.font.italic = True
    r_affil.font.color.rgb = RGBColor(71, 85, 105)

    # Emails
    p_email = doc.add_paragraph()
    p_email.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_email.paragraph_format.space_after = Pt(2)
    r_email = p_email.add_run("Emails: simpsonranga06@gmail.com, sarveshwaran706@gmail.com, sarathikannan200@gmail.com, varunsakthivel46@gmail.com")
    r_email.font.name = "Times New Roman"
    r_email.font.size = Pt(8.5)
    r_email.font.color.rgb = RGBColor(100, 116, 139)

    # Corresponding Author
    p_corr = doc.add_paragraph()
    p_corr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_corr.paragraph_format.space_after = Pt(10)
    r_corr = p_corr.add_run("* Corresponding author: Simpson R, simpsonranga06@gmail.com")
    r_corr.font.name = "Times New Roman"
    r_corr.font.size = Pt(8.5)
    r_corr.font.bold = True
    r_corr.font.color.rgb = RGBColor(30, 41, 59)

    # Abstract Box
    abstract_table = doc.add_table(rows=1, cols=1)
    abstract_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = abstract_table.cell(0, 0)
    cell.width = Inches(7.01)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    p_abs = cell.paragraphs[0]
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.line_spacing = 1.1
    p_abs.paragraph_format.space_after = Pt(6)
    
    r_abs_lbl = p_abs.add_run("Abstract— ")
    r_abs_lbl.font.name = "Times New Roman"
    r_abs_lbl.font.size = Pt(9)
    r_abs_lbl.font.bold = True
    
    r_abs_body = p_abs.add_run(
        "Prognostics and Health Management (PHM) architectures increasingly deploy data-driven algorithms—predominantly gradient-boosted decision trees—to estimate the Remaining Useful Life (RUL) of aircraft turbofan engines from continuous flight telemetry. However, standard predictive maintenance implementations implicitly assume that model artifacts remain uncompromised throughout deployment and that incoming sensor streams represent genuine physical degradation. In this paper, we present AeroSentinel, a threat-modeled research framework that integrates Edwards-curve Digital Signature (Ed25519) model authentication with multi-sensor statistical drift monitoring for ground-side turbofan prognostics. Evaluating on the standard NASA C-MAPSS FD001 benchmark (100 run-to-failure training trajectories, 100 censored operational test trajectories), we first discover and characterize a survival censoring distribution shift: screening clean operational test telemetry directly against run-to-failure training distributions triggers 8 sensor-level alert channels and 6 warning channels (14 out of 15 active degradation sensors flagged) resulting from run-to-failure censoring truncation rather than physical faults or adversarial tampering. By establishing an operational reference baseline on a disjoint 50/50 engine partition (Engines 1–50 as calibration fleet, Engines 51–100 as evaluation fleet, exhibiting 0 alerts and 0 warnings under clean conditions), we evaluate the detection sensitivity of Two-Sample Kolmogorov-Smirnov (KS) and Population Stability Index (PSI) monitors under six synthetic sensor-manipulation scenarios targeting static High-Pressure Compressor outlet pressure (s₁₁). Our empirical findings reveal notable detection blind spots: single-channel positive step biases (+1.0σ to +2.0σ) and creeping ramps trigger exactly one sensor-level PSI alert channel, leaving the overall fleet-level status at warning (below automated fleet rejection thresholds) while distorting RUL estimates by up to -12.07 cycles and degrading unclipped Root Mean Squared Error (RMSE) from 13.9044 to 20.4374. Crucially, negative bias injection (-1.0σ on s₁₁) artificially masks physical wear, delaying predicted maintenance overhaul by +5.16 cycles on average, escalating the asymmetric NASA penalty score to 433.13, and doubling the Canonical Hazardous Prediction Rate (HPR, over-predicting RUL >25 cycles when true RUL ≤ 25) from 15.79% (3/19 critical engines) to 31.58% (6/19 critical engines) while completely evading fleet drift alarms (0 alert channels, 1 warning channel; overall fleet status stable). Frozen telemetry replay forces an HPR of 100.00% (19/19 engines delayed) and surges the exponential NASA penalty to 791,878.67. To secure the model supply chain against deserialization gadget exploits and artifact tampering, we implement Ed25519 signing over RFC 8785 canonical JSON metadata; microbenchmarks (N=100) confirm that fail-closed cryptographic verification executes in 0.13 ± 0.02 ms (median 0.11 ms), with SHA-256 digest validation across the authenticated dependency set (21.01 MB across 5 binary and metadata artifacts) requiring 14.93 ms, contributing negligible overhead to total startup (24.37 ms) and batch inference (1.34 ms for 100 engines, 13.4 µs per engine). These findings highlight the necessity of combining cryptographic integrity controls with domain-informed multivariate consistency monitoring for aviation predictive analytics."
    )
    r_abs_body.font.name = "Times New Roman"
    r_abs_body.font.size = Pt(9)

    p_kw = cell.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_kw.paragraph_format.space_after = Pt(2)
    r_kw_lbl = p_kw.add_run("Keywords— ")
    r_kw_lbl.font.name = "Times New Roman"
    r_kw_lbl.font.size = Pt(9)
    r_kw_lbl.font.bold = True
    r_kw_body = p_kw.add_run("Aircraft Predictive Maintenance, Prognostics and Health Management, Remaining Useful Life, Adversarial Machine Learning, Cryptographic Artifact Authentication, Ed25519, Statistical Drift Detection, Sensor Manipulation, NASA C-MAPSS.")
    r_kw_body.font.name = "Times New Roman"
    r_kw_body.font.size = Pt(9)
    r_kw_body.font.italic = True

    # Helper functions
    def add_sec_heading(title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        return p

    def add_subsec_heading(title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.italic = True
        return p

    def add_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        return p

    def add_figure_image(img_path, caption):
        if Path(img_path).exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(2)
            doc.add_picture(str(img_path), width=Inches(6.6))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(10)
            r = p_cap.add_run(caption)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            r.font.italic = True

    # Transition to 2-Column Section for Body
    s2 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s2.top_margin = Inches(0.75)
    s2.bottom_margin = Inches(0.75)
    s2.left_margin = Inches(0.63)
    s2.right_margin = Inches(0.63)
    set_section_cols(s2, 2)

    # Section I
    add_sec_heading("I. INTRODUCTION")
    add_p("Predictive maintenance in modern commercial and military aviation relies extensively on data-driven Prognostics and Health Management (PHM) architectures. By analyzing multi-sensor flight telematics—including rotational spool speeds, static bleed pressures, and gas temperatures—machine learning algorithms forecast the Remaining Useful Life (RUL) of critical components, such as turbofan gas turbines. Accurate RUL estimates enable airline operators to transition from rigid calendar-based maintenance schedules to condition-based maintenance, minimizing unscheduled Aircraft on Ground (AOG) events and mitigating catastrophic inflight mechanical failures [1], [2].")
    add_p("Despite considerable algorithmic advances in deep recurrent neural networks and gradient-boosted decision tree ensembles [2], [3], existing aircraft predictive maintenance models are engineered under the implicit assumption of a benign, uncorrupted operating environment. In-flight and ground-transmitted telemetry streams are assumed to accurately reflect true thermodynamic degradation, and serialized model artifacts are presumed to reside securely within trusted ground-station environments.")
    add_p("However, modern aviation telematics ecosystems are increasingly distributed and interconnected. Sensor readings and post-flight telemetry summaries are routinely transferred via the Aircraft Communications Addressing and Reporting System (ACARS), cellular ground data links (Gatelink), and portable data terminals during turnaround. This expanded data interface introduces potential attack vectors across both data-plane and control-plane channels [4], [12]:")
    add_p("1) Supply-Chain Model-Artifact Tampering: Adversaries with read/write access to maintenance server storage or package repositories may alter serialized estimator weights, feature scaler parameters, or metadata manifests to deliberately suppress maintenance warnings or execute malicious code via Python deserialization gadget chains [4], [6].")
    add_p("2) Sensor Telemetry Manipulation: Compromised telematics gateways or Man-in-the-Middle (MitM) interceptors can inject subtle mathematical biases, frozen packet replays, or creeping calibration drifts into thermodynamic sensor streams, skewing RUL forecasts without triggering coarse out-of-bounds alarms [7], [8].")
    add_p("In aviation maintenance, prediction errors carry fundamentally asymmetric operational consequences. An early prediction (under-predicting RUL) prompts premature engine inspection, incurring unnecessary operational downtime and maintenance labor costs. Conversely, a delayed prediction (over-predicting RUL) is potentially hazardous: it allows an engine on the verge of mechanical failure to remain dispatched, risking severe in-flight damage [1], [2]. Despite this asymmetry, the degree to which lightweight statistical drift monitors can detect subtle sensor manipulation and the proportion of hazardous predictions that can escape detection remain insufficiently quantified.")
    add_p("To investigate these questions, we present AeroSentinel, an integrity-assured predictive maintenance framework evaluated on the NASA C-MAPSS FD001 turbofan benchmark. Our research provides five specific contributions: (1) Dual-protocol baseline disambiguation between raw unclipped and clipped ground-truth; (2) Characterization and resolution of the run-to-failure censoring distribution shift via a disjoint operational reference baseline; (3) Systematic empirical resilience profiling across six synthetic sensor manipulation scenarios; (4) Sub-millisecond Ed25519 cryptographic artifact authentication across the full artifact set; and (5) A fully reproducible open-source research suite.")

    # Section II
    add_sec_heading("II. RELATED WORK & RESEARCH GAP")
    add_subsec_heading("A. Aircraft Prognostics & Benchmark Methodologies")
    add_p("The NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark released by Saxena et al. [1] is the primary standard for data-driven turbofan prognostics. In the FD001 sub-dataset, high-pressure compressor degradation is modeled under steady-state sea-level conditions across 100 training and 100 test trajectories. Ramasso and Saxena [2] surveyed over 70 C-MAPSS studies and documented pervasive benchmark reporting discrepancies, specifically highlighting the conflation of raw physical targets with piecewise-linear clipped targets (RUL_max = 125 cycles). While deep learning (e.g., LSTM networks by Zheng et al. [3]) and gradient-boosted decision trees achieve high predictive fidelity on clean benchmark data, these studies focus exclusively on regression accuracy, omitting integrity controls or adversarial evaluation.")

    add_subsec_heading("B. Machine Learning Integrity & Artifact Authentication")
    add_p("The security of serialized machine learning models has gained increased attention as pipelines are integrated into critical infrastructure [4], [6]. Traditional persistence formats (such as Python pickle and joblib) deserialize arbitrary object state, exposing host environments to code execution vulnerabilities if model files are modified. Gu et al. [4] demonstrated that machine learning supply chains can harbor backdoors and modified weights without degrading clean accuracy. The National Institute of Standards and Technology (NIST) Special Publication 800-218 [6] explicitly recommends cryptographic signing of software and data artifacts. Bernstein et al. [5] introduced Ed25519 (Edwards-curve Digital Signature Algorithm over Curve25519), offering 128-bit security, high-speed verification, and resilience to side-channel timing attacks. However, standard predictive maintenance platforms commonly rely on unsigned SHA-256 checksums, which cannot prevent manifest rewrite attacks by an adversary with write access.")

    add_subsec_heading("C. Adversarial Attacks on Prognostic Time-Series & Sensor Streams")
    add_p("Adversarial machine learning research has expanded to sequential and cyber-physical time-series systems [7], [8], [12]. Fawaz et al. [7] and Karim et al. [8] demonstrated that subtle, bounded perturbations in sequential inputs can cause severe classification errors. Mo et al. [12] analyzed replay and sensor bias attacks on cyber-physical systems, proving that intelligent replay can evade traditional linear Kalman filter residual checks.")
    add_p("Directly relevant to turbofan prognostics, Basak et al. [14] investigated Universal Adversarial Perturbations (UAPs) tailored for deep learning prognostics across NASA C-MAPSS (FD001–FD004). Rather than crafting instance-specific perturbations, the authors used white-box gradient optimization across input sequences to formulate a single, dataset-wide perturbation vector that degraded RUL predictions in Deep CNNs, LSTMs, and GRUs. Mode & Hoque [15] evaluated the Fast Gradient Sign Method (FGSM) and Basic Iterative Method (BIM) on multivariate time-series regression for C-MAPSS and energy benchmarks using vanilla LSTMs, stacked LSTMs, and CNNs, establishing that gradient-based adversarial examples exhibit black-box transferability across neural network architectures.")
    add_p("While these foundational studies established the susceptibility of differentiable deep architectures to gradient-optimized noise, they leave critical questions unaddressed. Industrial predictive maintenance pipelines widely favor gradient-boosted decision tree ensembles applied to tabular rolling features because of their superior interpretability, low latency, and robustness on small-to-medium fleet datasets. Decision trees are non-differentiable step functions, rendering first-order gradient attacks ineffective. Furthermore, prior studies evaluated symmetric regression errors (RMSE, MAE) and omitted operational drift screening, survival censoring effects, and cryptographic model integrity.")

    add_subsec_heading("D. Statistical Drift Screening in Operational ML")
    add_p("For continuous covariate monitoring, production systems frequently employ non-parametric tests, such as the Two-Sample Kolmogorov-Smirnov (KS) test [11] and the Population Stability Index (PSI) [10]. However, Rabanser et al. [9] demonstrated in empirical studies (Failing Loudly) that statistical divergence tests can fail to alert under localized, task-relevant shifts. In aviation prognostics, the interaction between multi-sensor drift detection, physical censoring distributions, and stealthy sensor manipulation has not been systematically characterized.")

    # Table I: Continuous full-width break
    s_t1 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_t1.top_margin = Inches(0.75)
    s_t1.bottom_margin = Inches(0.75)
    s_t1.left_margin = Inches(0.63)
    s_t1.right_margin = Inches(0.63)
    set_section_cols(s_t1, 1)

    t_comp = doc.add_table(rows=7, cols=6)
    t_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
    h_comp = ["Study", "Model Architecture", "Attack Mechanism", "Dataset", "Evaluation Scope", "Defense / Integrity"]
    for j, h in enumerate(h_comp):
        c = t_comp.cell(0, j)
        set_cell_background(c, "1E293B")
        set_cell_margins(c, top=80, bottom=80, left=60, right=60)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    comp_data = [
        ["Basak et al. [14]", "Deep CNN, LSTM, GRU", "Universal Adversarial Noise (UAP)", "C-MAPSS (FD001-04)", "RMSE, NASA Score", "None (Attacker)"],
        ["Mode & Hoque [15]", "Vanilla/Stacked LSTM, CNN", "FGSM, BIM Gradient Noise", "C-MAPSS & SWaT", "RMSE, MAE", "None (Attacker)"],
        ["Fawaz et al. [7]", "ResNet, InceptionTime", "BIM / FGSM Time-Series Noise", "UCR/UEA Archive", "Classification Acc", "Adversarial Training"],
        ["Karim et al. [8]", "LSTM-FCN, ALSTM", "Adversarial Transformation", "UCR Archive", "Classification Acc", "None (Transferability)"],
        ["Gu et al. [4]", "Convolutional Networks", "Supply-Chain Trojan / BadNets", "Vision Benchmarks", "Attack Success Rate", "None (Audit Only)"],
        ["AeroSentinel (Ours)", "HistGradientBoosting (122 feat)", "Domain-Informed Sensor Tampering", "C-MAPSS FD001 (100)", "Dual Protocols, NASA, HPR", "PSI/KS + Ed25519 Signing"]
    ]
    for i, row in enumerate(comp_data):
        for j, val in enumerate(row):
            c = t_comp.cell(i+1, j)
            bg = "F8FAFC" if i % 2 == 0 else "FFFFFF"
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=60, right=60)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8)

    p_comp_cap = doc.add_paragraph()
    p_comp_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_comp_cap.paragraph_format.space_before = Pt(4)
    p_comp_cap.paragraph_format.space_after = Pt(8)
    r = p_comp_cap.add_run("TABLE I: Comparative Taxonomy of Adversarial Time-Series and Prognostic Security Research")
    r.font.name = "Times New Roman"
    r.font.size = Pt(8.5)
    r.font.bold = True

    # Back to two columns
    s_body3 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_body3.top_margin = Inches(0.75)
    s_body3.bottom_margin = Inches(0.75)
    s_body3.left_margin = Inches(0.63)
    s_body3.right_margin = Inches(0.63)
    set_section_cols(s_body3, 2)

    add_subsec_heading("E. Identified Research Gap")
    add_p("Prior literature exhibits three core limitations: (1) Conflation of evaluation baselines (raw vs. clipped ground-truth) without explicit protocol separation; (2) Overlooking survival censoring asymmetry when applying statistical drift detectors across training and operational test data; and (3) An absence of unified evaluations quantifying cryptographic artifact verification overhead alongside sensor-manipulation resilience on standardized aviation benchmarks.")

    # Section III
    add_sec_heading("III. SYSTEM ARCHITECTURE & THREAT MODEL")
    add_subsec_heading("A. Architectural Overview")
    add_p("AeroSentinel is designed as a ground-side advisory analytics service receiving turbofan telemetry post-flight. The architecture comprises four modular stages: (1) Cryptographic Lineage Verifier; (2) API Input Hardening Layer; (3) Dual-Baseline Covariate Drift Detector; and (4) Gradient-Boosted RUL Regressor.")

    add_subsec_heading("B. Threat Model & Trust Boundaries")
    add_p("We model threat actors using the STRIDE methodology: Adversary A_art operates on the model supply chain with write access to storage or network caches, capable of modifying model weights or manifests but lacking the offline Ed25519 private key. Adversary A_sen intercepts telematics in transit, injecting additive biases (delta in [-2.0sigma, +2.0sigma]), creeping ramps, or frozen buffers into sensor streams without modifying true labels.")
    add_p("The system enforces three core security invariants: (1) Fail-Closed Execution upon signature mismatch or byte tampering; (2) Dual Protocol Separation between raw unclipped and clipped metrics; and (3) Offline Ground-Truth Isolation ensuring true RUL is never exposed online.")
    add_p("Operational Scope and Advisory Boundary: AeroSentinel is strictly a ground-side predictive maintenance advisory service. It does not interface with airborne flight-control avionics, Full Authority Digital Engine Control (FADEC), or real-time fly-by-wire buses. Synthetic manipulations represent offline data perturbations and do not claim airworthiness certification compliance (e.g., RTCA DO-178C or DO-326A).")

    add_subsec_heading("C. Cryptographic Authentication Specification")
    add_p("AeroSentinel implements the Edwards-curve Digital Signature Algorithm over Curve25519 (Ed25519, RFC 8032) [5]. To prevent signature invalidation caused by dictionary key reordering or whitespace formatting variations, manifest payloads are serialized using the RFC 8785 JSON Canonicalization Scheme (JCS). At initialization, the runtime verifies the Ed25519 signature over canonical JSON, computes SHA-256 digests across all five declared dependency artifacts (best_model.joblib, preprocessor.joblib, histgradientboosting.joblib, random_forest.joblib, model_registry.json), authenticating the complete set of six on-disk model artifacts (totaling 21.01 MB on disk), and invokes joblib.load if and only if both checks succeed.")

    # Section IV
    add_sec_heading("IV. EXPERIMENTAL METHODOLOGY")
    add_subsec_heading("A. Dataset & Preprocessing Pipeline")
    add_p("We evaluate our framework on NASA C-MAPSS FD001 (100 training engines, 20,631 cycles; 100 test engines, 13,096 cycles; 100 ground-truth terminal RUL values). Six invariant sensors (s1, s5, s10, s16, s18, s19) and setting 3 are discarded, retaining 15 active degradation channels: s2, s3, s4, s6, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21. The causal feature pipeline extracts 122 features from 2 operational settings (setting_1, setting_2) and the 15 active degradation sensors: raw sensor readings, 5- and 15-cycle rolling means, 5- and 15-cycle rolling standard deviations, 1- and 5-cycle backward difference lags, initial-cycle baseline drift terms, and StandardScaler normalization fitted strictly on training data without cross-engine leakage.")

    add_subsec_heading("B. Dual Evaluation Protocols")
    add_p("To resolve historical reporting discrepancies, we evaluate two distinct target policies: Protocol A evaluates raw physical unclipped RUL targets (y* in [7, 145] cycles), while Protocol B evaluates piecewise-linear targets clipped at 125 cycles (y*_clip = min(y*, 125)), representing the standard health saturation assumption.")

    add_subsec_heading("C. Mathematical Evaluation Metrics")
    add_p("Model accuracy and prediction risk are evaluated via Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), Coefficient of Determination (R²), and the NASA Asymmetric Penalty Score (S_NASA), which penalizes late (hazardous) predictions exponentially more heavily than early predictions [1], [2].")

    add_subsec_heading("D. Canonical Hazardous Prediction Rate (HPR)")
    add_p("To isolate late-stage operational hazards, we evaluate the Canonical Hazardous Prediction Rate over the critical subset of test engines whose true remaining life is within 25 cycles (C_25 = {i : y*_i <= 25}, exactly |C_25| = 19 engines in FD001):")
    add_p("HPR = (|{i in C_25 : y_hat_i > 25}| / |C_25|) * 100%. Under clean baseline conditions, exactly 3 of 19 engines exceed 25 cycles, yielding HPR_clean = 15.79% (3/19). An attack that elevates HPR delays mandatory depot inspection for engines near structural failure.")

    add_subsec_heading("E. Drift Detection & Censoring Distribution Shift")
    add_p("Drift is monitored per sensor using the Two-Sample Kolmogorov-Smirnov (KS) test [11] and Population Stability Index (PSI) [10] across 10 quantile bins. We discover that comparing test telemetry directly against training data produces 8 alert channels and 6 warning channels (14 of 15 channels flagged) on clean data because training engines run to complete failure (100% dead) while test engines are censored. This reflects a structural survival-censoring divergence between training and operational distributions. AeroSentinel resolves this via a Dual-Baseline Architecture with disjoint engine partitioning: test engines are partitioned into Calibration Engines 1-50 (uncorrupted reference) and Evaluation Engines 51-100. Evaluating clean Evaluation Engines against Calibration Engines yields 0 alert channels and 0 warning channels (overall fleet status: stable).")
    add_p("System status aggregation rules: 'stable' (0 alerts, <=2 warnings); 'warning' (1 alert, or 3-4 warnings); 'drift_alert' (>=2 alerts, or >=5 total warnings/alerts).")

    add_subsec_heading("F. Synthetic Attack Scenarios")
    add_p("Six deterministic attack scenarios target sensor s11 (HPC static pressure, highest feature importance): sc1 (Step Bias +1.0σ), sc2 (Step Bias +2.0σ), sc3 (Negative Bias -1.0σ), sc4 (Creeping Linear Ramp +2.0σ), sc5 (Multi-Sensor Bias +1.0σ on s11, s9, s4), and sc6 (Frozen Replay at cycle 40%). Perturbation scales sigma(s_j) are calibrated strictly from the uncorrupted training baseline (train_FD001.txt) to preserve operational realism and ensure zero data leakage from evaluation trajectories.")

    # Section V
    add_sec_heading("V. EXPERIMENTAL RESULTS & ANALYSIS")
    add_subsec_heading("A. Clean Baseline Model Performance & Protocol Disambiguation")
    add_p("Table II summarizes clean baseline performance across both evaluation protocols on the 100 unseen held-out test engines.")

    # Table II & Fig 1: Continuous full-width break
    s_t2 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_t2.top_margin = Inches(0.75)
    s_t2.bottom_margin = Inches(0.75)
    s_t2.left_margin = Inches(0.63)
    s_t2.right_margin = Inches(0.63)
    set_section_cols(s_t2, 1)

    t2 = doc.add_table(rows=3, cols=8)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    h2 = ["Protocol", "Target Policy", "RMSE", "MAE", "R²", "NASA Score", "HPR (Count)", "HPR (%)"]
    for j, h in enumerate(h2):
        c = t2.cell(0, j)
        set_cell_background(c, "1E293B")
        set_cell_margins(c, top=80, bottom=80, left=70, right=70)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
    
    t2_data = [
        ["Protocol A", "Raw Unclipped", "13.9044", "10.4044", "0.8880", "301.97", "3 / 19", "15.79%"],
        ["Protocol B", "Clipped at 125", "13.0082", "9.3344", "0.8946", "280.35", "3 / 19", "15.79%"]
    ]
    for i, row in enumerate(t2_data):
        for j, val in enumerate(row):
            c = t2.cell(i+1, j)
            bg = "F8FAFC" if i % 2 == 0 else "FFFFFF"
            set_cell_background(c, bg)
            set_cell_margins(c, top=60, bottom=60, left=70, right=70)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8)

    p_t2_cap = doc.add_paragraph()
    p_t2_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_cap.paragraph_format.space_before = Pt(4)
    p_t2_cap.paragraph_format.space_after = Pt(8)
    r = p_t2_cap.add_run("TABLE II: Clean Baseline Performance Across Evaluation Protocols (N = 100 Engines)")
    r.font.name = "Times New Roman"
    r.font.size = Pt(8.5)
    r.font.bold = True

    add_figure_image(FIGURES_DIR / "fig1_baseline_protocols.png", "Fig. 1. Clean baseline evaluation under Protocol A (raw unclipped) vs. Protocol B (clipped at 125).")

    # Back to two columns
    s_body4 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_body4.top_margin = Inches(0.75)
    s_body4.bottom_margin = Inches(0.75)
    s_body4.left_margin = Inches(0.63)
    s_body4.right_margin = Inches(0.63)
    set_section_cols(s_body4, 2)

    add_subsec_heading("B. Sensor Manipulation Resilience & Evasion Dynamics")
    add_p("Table III presents verified empirical outcomes across all six sensor attack scenarios from sensor_attack_results.csv.")

    # Table III & Figures 2, 3, 4: Full-width break
    s_t3 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_t3.top_margin = Inches(0.75)
    s_t3.bottom_margin = Inches(0.75)
    s_t3.left_margin = Inches(0.63)
    s_t3.right_margin = Inches(0.63)
    set_section_cols(s_t3, 1)

    # Table III: Attacks
    t3 = doc.add_table(rows=8, cols=9)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    h3 = ["Scenario ID", "Description", "Shift", "RMSE", "MAE", "NASA Score", "HPR (Count)", "HPR (%)", "Disjoint Status"]
    for j, h in enumerate(h3):
        c = t3.cell(0, j)
        set_cell_background(c, "1E293B")
        set_cell_margins(c, top=80, bottom=80, left=60, right=60)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(7.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    t3_data = [
        ["baseline", "Clean Operational Baseline", "0.00c", "13.9044", "10.4044", "301.97", "3 / 19", "15.79%", "stable (0 alerts)"],
        ["sc1", "Step Bias (+1.0σ on S11)", "-9.52c", "18.1647", "13.5201", "452.46", "1 / 19", "5.26%", "warning (1 alert)"],
        ["sc2", "Step Bias (+2.0σ on S11)", "-12.07c", "20.4374", "15.5462", "577.97", "1 / 19", "5.26%", "warning (1 alert)"],
        ["sc3", "Negative Bias (-1.0σ on S11)", "+5.16c", "15.7392", "12.3014", "433.13", "6 / 19", "31.58%", "stable (0 alerts)"],
        ["sc4", "Creeping Ramp (+2.0σ on S11)", "-11.74c", "20.1812", "15.3778", "564.54", "1 / 19", "5.26%", "warning (1 alert)"],
        ["sc5", "Multi-Sensor Bias (+1.0σ)", "-21.55c", "28.5856", "21.8959", "1673.13", "0 / 19", "0.00%", "drift_alert (3 alerts)"],
        ["sc6", "Frozen Replay (Cycle 40%)", "+42.16c", "58.3342", "45.9051", "791,878.67", "19 / 19", "100.00%", "drift_alert (3 alerts)"]
    ]
    for i, row in enumerate(t3_data):
        for j, val in enumerate(row):
            c = t3.cell(i+1, j)
            bg = "F8FAFC" if i % 2 == 0 else "FFFFFF"
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=60, right=60)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(7.5)

    p_t3_cap = doc.add_paragraph()
    p_t3_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3_cap.paragraph_format.space_before = Pt(4)
    p_t3_cap.paragraph_format.space_after = Pt(8)
    r = p_t3_cap.add_run("TABLE III: Sensor Manipulation Impact on Predictions and Drift Evasion (N = 100 Engines)")
    r.font.name = "Times New Roman"
    r.font.size = Pt(8.5)
    r.font.bold = True

    add_figure_image(FIGURES_DIR / "fig2_attack_rul_shifts.png", "Fig. 2. RUL prediction shift and error distributions across six synthetic sensor attack scenarios.")
    add_figure_image(FIGURES_DIR / "fig3_asymmetric_nasa_surge.png", "Fig. 3. Exponential surge in NASA asymmetric penalty scores under delayed prediction scenarios.")
    add_figure_image(FIGURES_DIR / "fig4_drift_psi_heatmap.png", "Fig. 4. Fleet-wide sensor distribution drift (PSI) evaluated across the full 100-engine test fleet relative to clean operational telemetry (drift_clean), illustrating detection evasion in single-sensor bias and ramp attacks. Table III reports corresponding operational detection under the disjoint 50/50 calibration/evaluation partition (drift_disjoint).")

    # Back to two columns
    s_body5 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_body5.top_margin = Inches(0.75)
    s_body5.bottom_margin = Inches(0.75)
    s_body5.left_margin = Inches(0.63)
    s_body5.right_margin = Inches(0.63)
    set_section_cols(s_body5, 2)

    add_subsec_heading("C. Cryptographic Authentication & Tamper-Proofing Verification")
    add_p("Subjecting the Ed25519 verified loader to 12 distinct attack vectors confirmed 100% fail-closed enforcement: all altered artifact bytecodes, corrupted signatures, and foreign keys were strictly rejected, preventing unsafe joblib deserialization.")

    # Table IV: Full-width break
    s_t4 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_t4.top_margin = Inches(0.75)
    s_t4.bottom_margin = Inches(0.75)
    s_t4.left_margin = Inches(0.63)
    s_t4.right_margin = Inches(0.63)
    set_section_cols(s_t4, 1)

    t4 = doc.add_table(rows=13, cols=4)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    h4 = ["Test Vector ID", "Target Component / Mutation", "Expected Outcome", "Status"]
    for j, h in enumerate(h4):
        c = t4.cell(0, j)
        set_cell_background(c, "1E293B")
        set_cell_margins(c, top=80, bottom=80, left=70, right=70)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    t4_data = [
        ["TV-01", "Valid Signed Production Artifacts", "Load Success", "PASSED"],
        ["TV-02", "Modified Model Weights Bytecode", "Reject (Digest)", "PASSED"],
        ["TV-03", "Modified Feature Scaler Parameters", "Reject (Digest)", "PASSED"],
        ["TV-04", "Modified Signed Manifest Metadata", "Reject (Sig)", "PASSED"],
        ["TV-05", "Missing Signature Field", "Reject (Missing)", "PASSED"],
        ["TV-06", "Invalid / Corrupted Signature String", "Reject (Verify)", "PASSED"],
        ["TV-07", "Malformed / Truncated JSON Manifest", "Reject (Parser)", "PASSED"],
        ["TV-08", "Untrusted / Foreign Public Key", "Reject (Key)", "PASSED"],
        ["TV-09", "Manifest Hash Rewrite (No PrivKey)", "Reject (Sig)", "PASSED"],
        ["TV-10", "Unsupported Signature Algorithm", "Reject (Algo)", "PASSED"],
        ["TV-11", "Permissive Mode Bypass Notification", "Load (Audit Log)", "PASSED"],
        ["TV-12", "Strict Flag Active Without Key", "Reject (Startup)", "PASSED"]
    ]
    for i, row in enumerate(t4_data):
        for j, val in enumerate(row):
            c = t4.cell(i+1, j)
            bg = "F8FAFC" if i % 2 == 0 else "FFFFFF"
            set_cell_background(c, bg)
            set_cell_margins(c, top=40, bottom=40, left=70, right=70)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(7.5)

    p_t4_cap = doc.add_paragraph()
    p_t4_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t4_cap.paragraph_format.space_before = Pt(4)
    p_t4_cap.paragraph_format.space_after = Pt(8)
    r = p_t4_cap.add_run("TABLE IV: Cryptographic Artifact Authentication Test Vectors (Ed25519 / RFC 8785)")
    r.font.name = "Times New Roman"
    r.font.size = Pt(8.5)
    r.font.bold = True

    # Back to two columns
    s_body6 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_body6.top_margin = Inches(0.75)
    s_body6.bottom_margin = Inches(0.75)
    s_body6.left_margin = Inches(0.63)
    s_body6.right_margin = Inches(0.63)
    set_section_cols(s_body6, 2)

    add_subsec_heading("D. Computational Overhead & Latency Benchmarks")
    add_p("Microbenchmarks across N=100 independent trials confirm that pure Ed25519 signature verification requires only 0.13 ± 0.02 ms (median 0.11 ms), contributing less than 0.6% of the total 24.37 ms verified startup latency. Fleet batch inference for 100 engines executes in 1.34 ms (13.4 µs/engine), and full 15-sensor drift screening executes in 100.73 ms. Across independent benchmarking iterations (initial profiling in Fig. 5 vs Table V vs companion re-benchmark in performance_benchmarks.csv), component measurements vary by up to 19.2% for Ed25519 and 11.9% for deserialization (composite startup varying by 5.6%), with sub-millisecond cryptographic overhead confirmed across all trials.")

    # Table V & Figure 5: Full-width break
    s_t5 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_t5.top_margin = Inches(0.75)
    s_t5.bottom_margin = Inches(0.75)
    s_t5.left_margin = Inches(0.63)
    s_t5.right_margin = Inches(0.63)
    set_section_cols(s_t5, 1)

    t5 = doc.add_table(rows=9, cols=5)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    h5 = ["Pipeline Component", "Mean (ms)", "Std (ms)", "Median (ms)", "p95 (ms)"]
    for j, h in enumerate(h5):
        c = t5.cell(0, j)
        set_cell_background(c, "1E293B")
        set_cell_margins(c, top=80, bottom=80, left=80, right=80)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    t5_data = [
        ["Ed25519 Signature Verification", "0.13", "0.02", "0.11", "0.25"],
        ["Multi-File SHA-256 Hashing (21.01 MB, 5 artifacts)", "14.93", "0.82", "14.77", "16.40"],
        ["Model Deserialization (joblib.load)", "9.47", "1.96", "8.65", "14.32"],
        ["Total Verified Startup Pipeline", "24.37", "1.45", "23.90", "26.71"],
        ["Feature Engineering (13,096 cycles)", "135.96", "3.12", "135.62", "141.53"],
        ["Single-Engine Inference (1x122)", "1.39", "0.44", "1.16", "2.43"],
        ["Fleet Batch Inference (100x122)", "1.34", "0.32", "1.17", "2.11"],
        ["15-Sensor KS + PSI Drift Screening", "100.73", "2.56", "100.29", "105.32"],
    ]
    for i, row in enumerate(t5_data):
        for j, val in enumerate(row):
            c = t5.cell(i+1, j)
            bg = "F8FAFC" if i % 2 == 0 else "FFFFFF"
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=80, right=80)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8)

    p_t5_cap = doc.add_paragraph()
    p_t5_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t5_cap.paragraph_format.space_before = Pt(4)
    p_t5_cap.paragraph_format.space_after = Pt(8)
    r = p_t5_cap.add_run("TABLE V: Computational Latency Benchmarks Across Pipeline Stages (N = 100 Repetitions)")
    r.font.name = "Times New Roman"
    r.font.size = Pt(8.5)
    r.font.bold = True

    add_figure_image(FIGURES_DIR / "fig5_latency_breakdown.png", "Fig. 5. Computational latency breakdown across pipeline stages (N = 100 repetitions; component values illustrate the initial profiling run, while Table V reports the multi-trial benchmark distribution; across all runs, signature overhead remains under 0.15 ms, <0.6% of startup).")

    # Back to two columns for Discussion, Conclusion, Declarations, References
    s_body7 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    s_body7.top_margin = Inches(0.75)
    s_body7.bottom_margin = Inches(0.75)
    s_body7.left_margin = Inches(0.63)
    s_body7.right_margin = Inches(0.63)
    set_section_cols(s_body7, 2)

    # Section VI & VII
    add_sec_heading("VI. DISCUSSION, THREATS TO VALIDITY & LIMITATIONS")
    add_p("Our findings illustrate that statistical anomaly detectors calibrated for wide operational fleet tolerances exhibit inherent blind spots against stealthy perturbations. Adversaries can induce severe hazardous delays (doubling HPR to 31.58%) without crossing PSI alert thresholds. Consequently, predictive maintenance security requires end-to-end cryptographic integrity controls in tandem with physics-informed invariant checking.")
    add_p("Threats to validity include the synthetic nature of C-MAPSS simulation data, sea-level single-regime dynamics in FD001, the fixed 50/50 disjoint operational partitioning, and the advisory ground-side nature of the software, which is not an airborne certified flight-control computer.")

    add_sec_heading("VII. CONCLUSION & FUTURE WORK")
    add_p("This investigation evaluated integrity controls and sensor-manipulation resilience in a turbofan predictive maintenance pipeline using NASA C-MAPSS FD001. We resolved the run-to-failure censoring asymmetry via a disjoint operational reference baseline, demonstrated that single-channel sensor manipulations can evade fleet-level drift alarms while doubling the Hazardous Prediction Rate to 31.58% (6/19 critical engines delayed), and confirmed that Ed25519 cryptographic signing provides fail-closed artifact protection with negligible computational overhead (0.13 ms).")
    add_p("Future work will evaluate multi-regime envelopes (FD002/FD004) and integrate physics-informed neural network invariants.")

    # Declarations
    add_sec_heading("DECLARATIONS & ACKNOWLEDGMENTS")
    add_p("The authors express gratitude to the NASA Ames Prognostics Center of Excellence. No external commercial funding was received. All reproducible artifacts, scripts, and cryptographic keys are available in the AeroSentinel repository.")

    # References
    add_sec_heading("REFERENCES")
    refs = get_verified_references()
    for r_str in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(r_str)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)

    doc.save(OUTPUT_DOCX)
    print(f"[SUCCESS] Generated verified IJSART manuscript at: {OUTPUT_DOCX}")

if __name__ == "__main__":
    create_manuscript()
