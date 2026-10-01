import pymupdf, html

doc = pymupdf.open('/Users/andylulham/Documents/trammap/map.pdf')
page = doc[0]
DR = page.get_drawings()
W, H = 935.43, 1757.48

# ---------- helpers ----------
def f(v): return f"{v:.2f}".rstrip('0').rstrip('.')

def path_d(d, dx=0.0, dy=0.0):
    """Build an SVG path d-string from a pymupdf drawing's items."""
    out = []
    cur = None
    for it in d['items']:
        op = it[0]
        if op == 're':
            r = it[1]
            out.append(f"M{f(r.x0+dx)} {f(r.y0+dy)}h{f(r.width)}v{f(r.height)}h{f(-r.width)}Z")
            cur = None
            continue
        if op == 'qu':
            q = it[1]
            pts = [q.ul, q.ur, q.lr, q.ll]
            out.append("M" + " L".join(f"{f(p.x+dx)} {f(p.y+dy)}" for p in pts) + "Z")
            cur = None
            continue
        p0 = it[1]
        if cur is None or abs(cur.x-p0.x) > 0.05 or abs(cur.y-p0.y) > 0.05:
            out.append(f"M{f(p0.x+dx)} {f(p0.y+dy)}")
        if op == 'l':
            p1 = it[2]
            out.append(f"L{f(p1.x+dx)} {f(p1.y+dy)}")
            cur = p1
        elif op == 'c':
            p1, p2, p3 = it[2], it[3], it[4]
            out.append(f"C{f(p1.x+dx)} {f(p1.y+dy)} {f(p2.x+dx)} {f(p2.y+dy)} {f(p3.x+dx)} {f(p3.y+dy)}")
            cur = p3
    return "".join(out)

def glyph(idxs, box_idx):
    """White glyph paths of an icon, translated so the icon box origin is 0,0."""
    r = DR[box_idx]['rect']
    return "".join(f'<path d="{path_d(DR[i], -r.x0, -r.y0)}"/>' for i in idxs)

# ---------- colours ----------
INK = "#231f20"
BLUE, PURPLE, TT, YELLOW = "#005288", "#872175", "#404041", "#fdb924"
ICON = {  # key colour, bar tint, text colour
    'bus':      ("#1475bc", "#b9c9e7", "#094372", "Bus Interchange"),
    'train':    ("#e43131", "#f7c0ae", "#851310", "Train Interchange"),
    'pr':       ("#2b3594", "#b0add6", "#1e2171", "Park and Ride"),
    'cycle':    ("#05a1a5", "#bcdcde", "#005e61", "Cycle Parking"),
    'stadium':  ("#00716f", "#a2c8c8", "#004645", "Stadiums"),
    'uni':      ("#87452b", "#d2b6a7", "#57270f", "Universities/Colleges"),
    'hospital': ("#0079c1", "#adc8e9", "#004575", "West End Hospitals"),
}
GLYPHS = {
    'bus':      glyph([31], 30),
    'train':    glyph([36], 35),
    'pr':       glyph([27, 28, 29], 26),
    'cycle':    glyph([33, 34], 32),
    'stadium':  glyph([19], 18),
    'uni':      glyph([40, 41], 39),
    'hospital': glyph([38], 37),
}
BOX = 28.35
R_OUT, R_IN, R_DOT = 11.34, 10.2, 5.67

# ---------- route lines (exact paths from the PDF) ----------
LINE_IDX = {  # drawing indices in PDF paint order
    BLUE:   [42, 43, 44, 45, 46, 47],
    PURPLE: [48, 49, 50, 51, 52, 53, 54],
    TT:     [55, 56, 57, 58],
    YELLOW: [60, 61, 62, 63, 64, 65, 66],
}

# ---------- stations ----------
# x positions of line columns
YN, BN = 481.89, 453.54          # yellow / blue, north of city
PC, TC = 425.2, 510.24           # purple / tram train, city centre
BS, PS, PH = 396.85, 368.5, 311.8  # blue south, purple south, purple Herdings
YE, TE, YM = 538.58, 566.93, 623.62  # yellow east, tram train east, yellow Meadowhall

# Each station: name, y, dots [(x, colour)], label spec, icons, sub label, pill?
# label: (x, anchor)   anchor 'start' or 'end'
S = []
def stn(name, y, dots, lx, anchor='start', icons=(), sub=None, pill=False, lines2=None, sub_inline=None, icon_x=None):
    S.append(dict(name=name, y=y, dots=dots, lx=lx, anchor=anchor, icons=list(icons), sub=sub,
                  pill=pill, lines2=lines2, sub_inline=sub_inline, icon_x=icon_x))

L = 501.7
stn("Middlewood", 19.95, [(YN, YELLOW)], L, icons=['pr', 'cycle'], icon_x=646.4)
stn("Leppings Lane", 59.65, [(YN, YELLOW)], L)
stn("Malin Bridge", 90.8, [(BS, BLUE)], 377.0, 'end', icons=['pr', 'cycle'], icon_x=164.3)
stn("Hillsborough Park", 130.45, [(YN, YELLOW)], L)
stn("Hillsborough", 170.15, [(BN, BLUE), (YN, YELLOW)], L, icons=['bus', 'cycle'], sub="Interchange", pill=True, icon_x=654.7)
stn("Bamforth Street", 226.85, [(BN, BLUE), (YN, YELLOW)], L)
stn("Langsett/Primrose View", 266.55, [(BN, BLUE), (YN, YELLOW)], L)
stn("Infirmary Road", 306.25, [(BN, BLUE), (YN, YELLOW)], L)
stn("Shalesmoor for Kelham Island", 345.85, [(BN, BLUE), (YN, YELLOW)], L)
stn("Netherthorpe Road", 385.55, [(BN, BLUE), (YN, YELLOW)], L)
stn("University of Sheffield", 425.25, [(BN, BLUE), (YN, YELLOW)], L, icons=['uni', 'hospital'], icon_x=759.1)
stn("West Street", 464.95, [(BN, BLUE), (YN, YELLOW)], L)
stn("City Hall", 504.65, [(BN, BLUE), (YN, YELLOW)], L)
C4 = [(PC, PURPLE), (BN, BLUE), (YN, YELLOW), (TC, TT)]
stn("Cathedral", 544.35, C4, 530.1, pill=True)
stn("Castle Square", 584.05, C4, 530.1, icons=['bus'], icon_x=697.8)
stn("Fitzalan Square", 623.65, C4, 530.1, icons=['bus'], pill=True, icon_x=714.8)
# south (blue + purple)
SP = [(PS, PURPLE), (BS, BLUE)]
stn("Sheffield Station", 757.05, SP, 348.6, 'end', icons=['bus', 'train', 'cycle'], icon_x=58.2)
stn("Granville Road", 827.95, SP, 348.6, 'end')
stn("Park Grange Croft", 898.8, SP, 348.6, 'end')
stn("Park Grange", 938.5, SP, 348.6, 'end')
stn("Arbourthorne Road", 978.15, SP, 348.6, 'end')
stn("Spring Lane", 1017.85, SP, 348.6, 'end')
stn("Manor Top", 1057.55, SP, 348.6, 'end')
stn("Hollinsend", 1097.25, SP, 348.6, 'end')
stn("Gleadless Townend", 1136.9, SP, 348.6, 'end', pill=True)
stn("Herdings/", 1216.15, [(PH, PURPLE)], 291.9, 'end', lines2="Leighton Road")
stn("Herdings Park", 1255.85, [(PH, PURPLE)], 291.9, 'end')
B1 = [(BS, BLUE)]
stn("White Lane", 1306.85, B1, 377.0, 'end')
stn("Birley Lane", 1346.55, B1, 377.0, 'end')
stn("Birley Moor Road", 1386.25, B1, 377.0, 'end')
stn("Hackenthorpe", 1425.9, B1, 377.0, 'end')
stn("Donetsk Way", 1465.6, B1, 377.0, 'end')
stn("Moss Way", 1505.3, B1, 377.0, 'end')
stn("Crystal Peaks", 1544.95, B1, 377.0, 'end', icons=['bus'], sub="Interchange", icon_x=184.7)
stn("Drake House Lane", 1601.65, B1, 377.0, 'end', sub="Beighton")
stn("Waterthorpe", 1658.35, B1, 377.0, 'end')
stn("Westfield", 1698.05, B1, 377.0, 'end')
stn("Halfway", 1737.75, B1, 377.0, 'end', icons=['pr', 'cycle'], icon_x=216.2)
# east (yellow + tram train)
E = 586.8
ET = [(YE, YELLOW), (TE, TT)]
stn("Hyde Park", 756.95, ET, E)
stn("Cricket Inn Road", 796.65, ET, E)
stn("Nunnery Square", 836.3, ET, E, icons=['pr', 'cycle'], icon_x=780.3)
stn("Woodbourn Road", 876.0, ET, E)
stn("Attercliffe", 946.85, ET, E)
stn("Arena ", 986.55, ET, E, sub_inline="Olympic Legacy Park")
stn("Valley Centertainment", 1057.4, ET, E, icons=['pr', 'cycle'], icon_x=848.1)
stn("Carbrook ", 1097.1, ET, E, icons=['pr'], sub_inline="for IKEA", icon_x=782.4)
stn("Meadowhall South", 1136.8, ET, E, sub="Tinsley", pill=True)
stn("Meadowhall", 1227.5, [(YM, YELLOW)], 643.5, icons=['bus', 'train', 'pr', 'cycle'], sub="Interchange", icon_x=786.5)
stn("Magna", 1295.55, [(TE, TT)], E, icons=['pr', 'cycle'], icon_x=671.8)
stn("Rotherham Central", 1352.2, [(TE, TT)], E, icons=['bus', 'train', 'cycle'], icon_x=813.2)
stn("Parkgate", 1391.9, [(TE, TT)], E, icons=['pr', 'cycle'], icon_x=697.0)

# tags: (kind, text, anchor x, y0, anchor)  anchor 'start' => icon box at x; 'end' => bar ends at x
TAGS = [  # last field: the stop the tag belongs to
    ('stadium', "Hillsborough Stadium", 501.7, 79.5, 'start', 704.9, "Leppings Lane"),
    ('stadium', "Ponds Forge", 530.1, 641.2, 'start', 665.9, "Fitzalan Square"),
    ('uni', "Sheffield Hallam University", 351.5, 774.5, 'end', 111.3, "Sheffield Station"),
    ('stadium', "Bramall Lane", 9.1, 845.4, 'start', 147.5, "Granville Road"),
    ('uni', "The Sheffield College", 351.5, 845.4, 'end', 153.2, "Granville Road"),
    ('stadium', "City Athletics Stadium", 586.8, 893.5, 'start', 790.6, "Woodbourn Road"),
    ('stadium', "Sheffield Arena", 586.8, 1004.0, 'start', 743.3, "Arena"),
]

# ---------- fare zones ----------
ZONES = [
    (1, "Malin Bridge/Middlewood to Infirmary Road"),
    (2, "Infirmary Road to University of Sheffield"),
    (3, "University of Sheffield to Granville Road/Hyde Park"),
    (4, "Hyde Park to Nunnery Square"),
    (5, "Nunnery Square to Arena (Olympic Legacy Park)"),
    (6, "Arena (Olympic Legacy Park) to Meadowhall Interchange"),
    (7, "Meadowhall South (Tinsley) to Parkgate"),
    (8, "Granville Road to Spring Lane"),
    (9, "Spring Lane to White Lane/Herdings Park"),
    (10, "White Lane to Crystal Peaks Interchange"),
    (11, "Crystal Peaks Interchange to Halfway"),
]
# boundary y values (station centres)
yInf, yUni, yGran, yHyde, yNun, yArena, yMS, ySpr, yWL, yCP = 306.25, 425.25, 827.95, 756.95, 836.3, 986.55, 1136.8, 1017.85, 1306.85, 1544.95
XL, XS, XP = 300, 467, 583   # left margin wall, west/east split, Meadowhall pocket wall
REGIONS = {
    1:  [(150, 0), (W, 0), (W, yInf), (XL, yInf), (XL, 125), (150, 125)],
    2:  [(XL, yInf), (W, yInf), (W, yUni), (XL, yUni)],
    3:  [(XL, yUni), (W, yUni), (W, yHyde), (XS, yHyde), (XS, yGran), (0, yGran), (0, 625), (XL, 625)],
    4:  [(XS, yHyde), (W, yHyde), (W, yNun), (XS, yNun)],
    5:  [(XS, yNun), (W, yNun), (W, yArena), (XS, yArena)],
    6:  [(XS, yArena), (W, yArena), (W, 1268), (XP, 1268), (XP, yMS), (XS, yMS)],
    7:  [(XS, yMS), (XP, yMS), (XP, 1268), (W, 1268), (W, 1425), (XS, 1425)],
    8:  [(0, yGran), (XS, yGran), (XS, ySpr), (0, ySpr)],
    9:  [(0, ySpr), (XS, ySpr), (XS, yWL), (0, yWL)],
    10: [(0, yWL), (XS, yWL), (XS, yCP), (0, yCP)],
    11: [(0, yCP), (XS, yCP), (XS, H), (0, H)],
}
ZLABEL = {1: (345, 232), 2: (345, 366), 3: (345, 520), 4: (885, 797), 5: (885, 912), 6: (885, 1122),
          7: (885, 1300), 8: (62, 940), 9: (62, 1200), 10: (62, 1425), 11: (62, 1650)}
TINT = {'a': 'var(--zone-a)', 'b': 'var(--zone-b)'}
ZTINT = {z: ('a' if z % 2 else 'b') for z in range(1, 12)}  # tree adjacency is bipartite on parity

# ---------- network connectivity (for the short-journey finder) ----------
NORTH = ["Hillsborough", "Bamforth Street", "Langsett/Primrose View", "Infirmary Road", "Shalesmoor for Kelham Island",
         "Netherthorpe Road", "University of Sheffield", "West Street", "City Hall", "Cathedral", "Castle Square", "Fitzalan Square"]
SOUTH = ["Sheffield Station", "Granville Road", "Park Grange Croft", "Park Grange", "Arbourthorne Road", "Spring Lane",
         "Manor Top", "Hollinsend", "Gleadless Townend"]
EAST = ["Hyde Park", "Cricket Inn Road", "Nunnery Square", "Woodbourn Road", "Attercliffe", "Arena",
        "Valley Centertainment", "Carbrook", "Meadowhall South"]
LINES = {
    "Yellow": ["Middlewood", "Leppings Lane", "Hillsborough Park"] + NORTH + EAST + ["Meadowhall"],
    "Blue": ["Malin Bridge"] + NORTH + SOUTH + ["White Lane", "Birley Lane", "Birley Moor Road", "Hackenthorpe",
                                                "Donetsk Way", "Moss Way", "Crystal Peaks", "Drake House Lane",
                                                "Waterthorpe", "Westfield", "Halfway"],
    "Purple": ["Cathedral", "Castle Square", "Fitzalan Square"] + SOUTH + ["Herdings/", "Herdings Park"],
    "Tram Train": ["Cathedral", "Castle Square", "Fitzalan Square"] + EAST + ["Magna", "Rotherham Central", "Parkgate"],
}
# Stops in each fare zone (boundary stops appear in two zones), from zones.md
ZONE_STOPS = {
    1: ["Malin Bridge", "Middlewood", "Leppings Lane", "Hillsborough Park", "Hillsborough", "Bamforth Street", "Langsett/Primrose View", "Infirmary Road"],
    2: ["Infirmary Road", "Shalesmoor for Kelham Island", "Netherthorpe Road", "University of Sheffield"],
    3: ["University of Sheffield", "West Street", "City Hall", "Cathedral", "Castle Square", "Fitzalan Square", "Sheffield Station", "Granville Road", "Hyde Park"],
    4: ["Hyde Park", "Cricket Inn Road", "Nunnery Square"],
    5: ["Nunnery Square", "Woodbourn Road", "Attercliffe", "Arena"],
    6: ["Arena", "Valley Centertainment", "Carbrook", "Meadowhall South", "Meadowhall"],
    7: ["Meadowhall South", "Magna", "Rotherham Central", "Parkgate"],
    8: ["Granville Road", "Park Grange Croft", "Park Grange", "Arbourthorne Road", "Spring Lane"],
    9: ["Spring Lane", "Manor Top", "Hollinsend", "Gleadless Townend", "Herdings/", "Herdings Park", "White Lane"],
    10: ["White Lane", "Birley Lane", "Birley Moor Road", "Hackenthorpe", "Donetsk Way", "Moss Way", "Crystal Peaks"],
    11: ["Crystal Peaks", "Drake House Lane", "Waterthorpe", "Westfield", "Halfway"],
}
KEYS = [s['name'].strip() for s in S]
STOP_ZONES = {k: sorted(z for z, stops in ZONE_STOPS.items() if k in stops) for k in KEYS}
for k, zs in STOP_ZONES.items():
    assert 1 <= len(zs) <= 2, (k, zs)
for stops in LINES.values():
    for k in stops:
        assert k in STOP_ZONES, k
# hops: each pair of neighbouring stops, with the single zone that hop lies in
HOPS = {}
for stops in LINES.values():
    for a, b in zip(stops, stops[1:]):
        shared = set(STOP_ZONES[a]) & set(STOP_ZONES[b])
        assert len(shared) == 1, (a, b, shared)
        HOPS[tuple(sorted((a, b)))] = shared.pop()
DISPLAY = {s['name'].strip(): (s['name'].strip() + s['lines2']) if s['lines2'] else s['name'].strip() for s in S}
import json
NETWORK = json.dumps({
    "stops": {k: {"zones": STOP_ZONES[k], "name": DISPLAY[k]} for k in KEYS},
    "hops": [[a, b, z] for (a, b), z in HOPS.items()],
    "lines": LINES,
    "lineColours": {"Blue": BLUE, "Purple": PURPLE, "Tram Train": TT, "Yellow": YELLOW},
}, separators=(',', ':'))

# ---------- build SVG ----------
o = []
A = o.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="map-title map-desc" font-family="Figtree, \'Helvetica Neue\', Arial, sans-serif">')
A('<title id="map-title">Sheffield Supertram network map with fare zones</title>')
A('<desc id="map-desc">Schematic map of the Supertram Blue, Purple, Yellow and Tram Train routes, with the eleven fare zones shown as shaded bands behind the lines.</desc>')
A('<defs>')
for k, (bg, bar, txt, label) in ICON.items():
    A(f'<symbol id="ic-{k}" viewBox="0 0 {BOX} {BOX}"><rect width="{BOX}" height="{BOX}" rx="2.83" fill="{bg}"/><g fill="#fff">{GLYPHS[k]}</g></symbol>')
A('</defs>')

# zones
A('<g id="zones">')
for z, pts in REGIONS.items():
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"
    A(f'<path class="zone zone-{ZTINT[z]}" data-zone="{z}" d="{d}"/>')
for z, (x, y) in ZLABEL.items():
    A(f'<text class="zone-num" x="{x}" y="{y}" text-anchor="middle" dominant-baseline="central">{z}</text>')
A('</g>')

# route lines
A('<g id="lines" fill="none" stroke-width="11.34" stroke-linecap="round" stroke-linejoin="round">')
for col, idxs in LINE_IDX.items():
    if col == YELLOW:
        A(f'<path d="{path_d(DR[59])}" stroke="#fff"/>')  # white bridge where Yellow crosses Tram Train
    for i in idxs:
        A(f'<path d="{path_d(DR[i])}" stroke="{col}"/>')
A('</g>')

# station markers
A('<g id="stations">')
for s in S:
    y = s['y']; xs = [d[0] for d in s['dots']]
    g = []
    if s['pill'] and len(xs) > 1:
        x1, x2 = min(xs), max(xs)
        g.append(f'<rect x="{f(x1)}" y="{f(y-R_DOT)}" width="{f(x2-x1)}" height="{f(2*R_DOT)}" fill="{INK}"/>')
    for x in xs:
        g.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{R_OUT}" fill="{INK}"/>')
    if s['pill'] and len(xs) > 1:
        g.append(f'<rect x="{f(x1)}" y="{f(y-4.54)}" width="{f(x2-x1)}" height="9.08" fill="#fff"/>')
    for x in xs:
        g.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{R_IN}" fill="#fff"/>')
    for x, c in s['dots']:
        g.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{R_DOT}" fill="{c}"/>')
    key = s['name'].strip()
    halo = f'<rect class="halo" x="{f(min(xs)-17)}" y="{f(y-17)}" width="{f(max(xs)-min(xs)+34)}" height="34" rx="17"/>'
    A(f'<g class="stn" data-name="{html.escape(key)}" tabindex="0" role="button" aria-label="{html.escape(DISPLAY[key])}: show stops within a short journey">{halo}{"".join(g)}</g>')
A('</g>')

# labels + icons
A(f'<g id="labels" fill="{INK}">')
for s in S:
    y = s['y']; name = s['name']
    anchor = s['anchor']
    tx = s['lx']
    inner = html.escape(name)
    if s['sub_inline']:
        inner += f'<tspan class="sub">{html.escape(s["sub_inline"])}</tspan>'
    sid = html.escape(name.strip())
    A(f'<g class="lbl" data-name="{sid}">')
    if s['lines2']:
        A(f'<text class="name" x="{tx}" y="{f(y-28.3)}" text-anchor="{anchor}" dominant-baseline="central">{inner}</text>')
        A(f'<text class="name" x="{tx}" y="{f(y-0.7)}" text-anchor="{anchor}" dominant-baseline="central">{html.escape(s["lines2"])}</text>')
    else:
        A(f'<text class="name" id="lbl-{sid}" x="{tx}" y="{f(y-0.7)}" text-anchor="{anchor}" dominant-baseline="central">{inner}</text>')
    if s['sub']:
        A(f'<text class="sub" x="{tx}" y="{f(y+24)}" text-anchor="{anchor}" dominant-baseline="central">{html.escape(s["sub"])}</text>')
    if s['icons']:
        ix = s['icon_x']
        A(f'<g class="icons" data-label="lbl-{sid}" data-anchor="{anchor}" data-x="{f(ix)}">')
        for k, ic in enumerate(s['icons']):
            A(f'<use href="#ic-{ic}" x="{f(ix + k*34)}" y="{f(y - BOX/2 + 0.1)}" width="{BOX}" height="{BOX}"><title>{ICON[ic][3]}</title></use>')
        A('</g>')
    A('</g>')
A('</g>')

# tags (stadium / university labels)
A('<g id="tags">')
for kind, text, ax, y0, anchor, other, stop in TAGS:
    bg, bar, tcol, _ = ICON[kind]
    if anchor == 'start':
        x0 = ax; bar_end = other
    else:
        x0 = other; bar_end = ax
    A(f'<g class="tag" data-anchor="{anchor}" data-ax="{f(ax)}" data-stop="{html.escape(stop)}">')
    A(f'<rect class="tag-bar" x="{f(x0+7.4)}" y="{f(y0)}" width="{f(bar_end-x0-7.4)}" height="{BOX}" rx="2.83" fill="{bar}"/>')
    A(f'<use href="#ic-{kind}" x="{f(x0)}" y="{f(y0)}" width="{BOX}" height="{BOX}"/>')
    A(f'<text class="tag-text" x="{f(x0+34)}" y="{f(y0+BOX/2-0.3)}" fill="{tcol}" dominant-baseline="central">{html.escape(text)}</text>')
    A('</g>')
A('</g>')

# key box
A('<g id="key">')
A('<rect x="43.2" y="158.8" width="229.6" height="442.2" rx="5.6" fill="#f7f2e8"/>')
A(f'<text class="h" x="58.3" y="182" fill="{INK}" dominant-baseline="central">Routes</text>')
for yy, col, label in [(212.1, BLUE, "Blue"), (239.0, PURPLE, "Purple"), (265.8, TT, "Tram Train"), (292.6, YELLOW, "Yellow")]:
    A(f'<path d="M61.1 {yy}H100.8" stroke="{col}" stroke-width="10"/>')
    A(f'<text class="k" x="106.5" y="{f(yy-1.7)}" fill="{INK}" dominant-baseline="central">{label}</text>')
A(f'<text class="h" x="58.3" y="332.75" fill="{INK}" dominant-baseline="central">Key</text>')
for k, kind in enumerate(['bus', 'train', 'pr', 'cycle', 'stadium', 'uni', 'hospital']):
    bg, bar, tcol, label = ICON[kind]
    y0 = 353.7 + k*34.03
    A(f'<rect x="61.9" y="{f(y0)}" width="195.8" height="{BOX}" rx="2.83" fill="{bar}"/>')
    A(f'<use href="#ic-{kind}" x="58.3" y="{f(y0)}" width="{BOX}" height="{BOX}"/>')
    A(f'<text class="k" x="92.3" y="{f(y0+BOX/2-0.3)}" fill="{tcol}" dominant-baseline="central">{label}</text>')
A('</g>')
A('</svg>')
SVG = "\n".join(o)

HTML = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supertram Network Map with Fare Zones</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink: {INK};
    --paper: #ffffff;
    --zone-a: #e4ebf2;
    --zone-b: #f3eee4;
    --zone-num: #a4aeb8;
    --panel: #f7f2e8;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; background: var(--paper); color: var(--ink); font-family: Figtree, "Helvetica Neue", Arial, sans-serif; }}
  header {{ padding: 20px 24px 8px; display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 18px; }}
  header h1 {{ font-size: 22px; font-weight: 600; margin: 0; }}
  header p {{ margin: 0; font-size: 14px; color: #5a5a5a; }}
  .layout {{ display: grid; grid-template-columns: minmax(0, 935px) minmax(260px, 340px); gap: 24px; padding: 8px 24px 40px; max-width: 1340px; }}
  .map {{ min-width: 0; }}
  .map svg {{ width: 100%; height: auto; display: block; touch-action: manipulation; }}
  /* side panel: lists the stops you can reach from the selected stop (desktop only) */
  aside {{ position: sticky; top: 16px; align-self: start; max-height: calc(100vh - 32px); overflow-y: auto; background: var(--panel); border-radius: 8px; padding: 18px 18px 16px; }}
  aside h2 {{ font-size: 20px; font-weight: 500; margin: 0 0 8px; }}
  aside p {{ font-size: 14px; line-height: 1.4; margin: 10px 0 0; }}
  aside .note {{ color: #5a5a5a; border-top: 1px solid #e3dccd; padding-top: 10px; }}
  aside .note + .note {{ border-top: 0; padding-top: 0; }}
  ol.reach-list {{ list-style: none; margin: 12px 0 14px; padding: 0; }}
  ol.reach-list:empty {{ display: none; }}
  .rl {{ display: flex; align-items: center; gap: 10px; padding: 5px 8px; border-radius: 6px; font-size: 14px; line-height: 1.3; background: #fff; margin-bottom: 3px; }}
  .rl-lines {{ flex: 0 0 24px; display: flex; gap: 3px; }}  /* fixed width so names line up whether one or two lines serve the stop */
  .rl-lines i {{ display: block; width: 10px; height: 10px; border-radius: 50%; }}
  .rl-name {{ flex: 1 1 auto; }}
  .rl-zone {{ flex: 0 0 auto; font-size: 12px; font-weight: 600; color: #5f6b77; background: var(--zone-a); border-radius: 10px; padding: 1px 8px; }}
  .rl-zone.two {{ background: linear-gradient(90deg, var(--zone-a) 50%, var(--zone-b) 50%); }}
  /* SVG text styles */
  .name {{ font-size: 23px; font-weight: 500; }}
  .sub {{ font-size: 18px; font-weight: 400; }}
  .tag-text, .k {{ font-size: 16px; font-weight: 400; }}
  .h {{ font-size: 23px; font-weight: 500; }}
  .zone {{ stroke: #fff; stroke-width: 1.5; stroke-linejoin: round; }}
  .zone-a {{ fill: var(--zone-a); }}
  .zone-b {{ fill: var(--zone-b); }}
  .zone-num {{ font-size: 64px; font-weight: 600; fill: var(--zone-num); letter-spacing: -0.02em; }}
  .zone-num-sm {{ font-size: 18px; }}
  /* short-journey finder */
  /* Desktop: sticks to the top of the map column while scrolling. Reserves two lines so the map never shifts. */
  .status {{ position: sticky; top: 0; z-index: 5; margin: 0 0 10px; padding: 6px 0; min-height: 54px; font-size: 15px; line-height: 21px; color: #4a4a4a; background: var(--paper); }}
  .status strong {{ color: var(--ink); font-weight: 600; }}
  .status .clear {{ margin-left: 8px; font: inherit; font-size: 13px; line-height: 17px; height: 19px; padding: 0 10px; vertical-align: top; color: #094372; background: none; border: 1px solid #094372; border-radius: 10px; cursor: pointer; }}  /* shorter than the line box, so it cannot grow the line */
  /* Phones and tablets: a fixed bar at the bottom of the screen, within thumb reach. */
  @media (max-width: 1000px) {{
    .status {{ position: fixed; left: 0; right: 0; bottom: 0; top: auto; margin: 0; min-height: 0; padding: 10px 16px calc(10px + env(safe-area-inset-bottom)); font-size: 14px; line-height: 19px; background: rgba(255,255,255,.96); border-top: 1px solid #ddd; box-shadow: 0 -2px 10px rgba(0,0,0,.08); }}
    body {{ padding-bottom: 96px; }}
  }}
  .stn, .lbl {{ cursor: pointer; }}
  .stn:focus {{ outline: none; }}
  .stn, .lbl, .zone, .zone-num {{ transition: opacity .18s ease, fill .18s ease; }}
  /* Also doubles as a larger invisible tap target around each marker (opacity 0 still receives pointer events). */
  .halo {{ fill: rgba(0,0,0,0); stroke: var(--ink); stroke-width: 2.6; stroke-dasharray: 4 3; opacity: 0; transition: opacity .18s ease; pointer-events: fill; }}
  svg.active .stn:not(.reach), svg.active .lbl:not(.reach), svg.active .tag:not(.reach) {{ opacity: .22; }}
  .tag {{ transition: opacity .18s ease; }}
  svg.active .stn.origin .halo, .stn:focus-visible .halo {{ opacity: 1; }}
  svg.active .zone-a:not(.lit), svg.active .zone-b:not(.lit) {{ fill: #f6f6f5; }}
  svg.active .zone-num:not(.lit) {{ opacity: .35; }}
  svg.active .zone-a.lit {{ fill: #d3e0ee; }}
  svg.active .zone-b.lit {{ fill: #ece2cc; }}
  svg.active .zone-num.lit {{ fill: #7d8a98; }}
  @media (max-width: 1000px) {{
    .layout {{ grid-template-columns: 1fr; }}
    aside {{ display: none; }}  /* the fixed status bar does this job on small screens */
  }}
  @media print {{
    header, aside {{ display: none; }}
    .layout {{ padding: 0; display: block; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Supertram network map</h1>
  <p>Routes, interchanges and fare zones. Based on the Supertram Network Map (April 2026).</p>
</header>
<div class="layout">
  <div class="map">
    <p class="status" id="status" aria-live="polite">Tap a stop to see every stop you can reach on a short journey (1 or 2 fare zones).</p>
{SVG}
  </div>
  <aside id="panel">
    <h2 id="panel-title">Short journey finder</h2>
    <p id="panel-intro">Hover over a stop on the map to list every stop you can reach on a short journey ticket: 1 or 2 fare zones, without changing tram. Click a stop to keep it selected.</p>
    <ol class="reach-list" id="reach-list"></ol>
    <p class="note">A stop shown on a boundary between two shaded bands is in both fare zones.</p>
    <p class="note">A <strong>short journey</strong> is a journey within 1 or 2 fare zones. A <strong>longer journey</strong> is a journey in more than 2 fare zones.</p>
  </aside>
</div>
<script>
// Once the web font is available, snap icons and tag bars to the measured text widths so
// nothing overlaps or leaves a gap if the fallback font has different metrics.
(function () {{
  const GAP = 6, STEP = 34, BOX = {BOX};
  function layout() {{
    document.querySelectorAll('g.icons').forEach(g => {{
      const t = document.getElementById(g.dataset.label);
      if (!t) return;
      const bb = t.getBBox();
      const uses = g.querySelectorAll('use');
      let x0;
      if (g.dataset.anchor === 'start') x0 = bb.x + bb.width + GAP;
      else x0 = bb.x - GAP - (uses.length - 1) * STEP - BOX;
      uses.forEach((u, i) => u.setAttribute('x', (x0 + i * STEP).toFixed(2)));
    }});
    document.querySelectorAll('g.tag').forEach(g => {{
      const text = g.querySelector('.tag-text'), bar = g.querySelector('.tag-bar'), icon = g.querySelector('use');
      const w = text.getComputedTextLength();
      const ax = parseFloat(g.dataset.ax);
      let x0 = g.dataset.anchor === 'start' ? ax : ax - (34 + w + GAP);
      icon.setAttribute('x', x0.toFixed(2));
      text.setAttribute('x', (x0 + 34).toFixed(2));
      bar.setAttribute('x', (x0 + 7.4).toFixed(2));
      bar.setAttribute('width', (34 + w + GAP - 7.4).toFixed(2));
    }});
  }}
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout); else layout();
}})();

// Short-journey finder. The network is a tree, so each pair of stops has one path; a stop is
// within a short journey when that path crosses no more than two distinct fare zones.
(function () {{
  const NET = {NETWORK};
  const MAX_ZONES = 2;
  const svg = document.querySelector('.map svg');
  const status = document.getElementById('status');
  const DEFAULT = status.innerHTML;
  const adj = {{}};
  NET.hops.forEach(([a, b, z]) => {{
    (adj[a] = adj[a] || []).push([b, z]);
    (adj[b] = adj[b] || []).push([a, z]);
  }});
  const stnEls = {{}}, lblEls = {{}};
  svg.querySelectorAll('g.stn').forEach(g => stnEls[g.dataset.name] = g);
  svg.querySelectorAll('g.lbl').forEach(g => lblEls[g.dataset.name] = g);
  const tagEls = [...svg.querySelectorAll('g.tag')];
  const zoneEls = {{}};
  svg.querySelectorAll('.zone').forEach(p => zoneEls[p.dataset.zone] = [p]);
  svg.querySelectorAll('#zones .zone-num').forEach(t => zoneEls[t.textContent].push(t));

  const ALLOW_CHANGES = false;  // true: any route counts; false: a journey must stay on one tram
  const hopZone = {{}};
  NET.hops.forEach(([a, b, z]) => {{ hopZone[a + '|' + b] = z; hopZone[b + '|' + a] = z; }});

  function reachable(origin) {{
    // returns {{stop: {{zones: Set of zones crossed, hops: stops travelled, lines: Set of lines}}}}
    // for every stop within MAX_ZONES of the origin
    const seen = {{ [origin]: {{ zones: new Set(), hops: 0, lines: new Set() }} }};
    if (ALLOW_CHANGES) {{
      // breadth-first walk over the whole network, carrying the zones used so far
      const queue = [origin];
      while (queue.length) {{
        const cur = queue.shift();
        for (const [next, z] of adj[cur] || []) {{
          if (next in seen) continue;
          const zones = new Set(seen[cur].zones); zones.add(z);
          if (zones.size > MAX_ZONES) continue;
          seen[next] = {{ zones, hops: seen[cur].hops + 1, lines: new Set() }};
          queue.push(next);
        }}
      }}
      return seen;
    }}
    // single tram: walk each line that serves the origin, outwards in both directions
    for (const [line, stops] of Object.entries(NET.lines)) {{
      const i = stops.indexOf(origin);
      if (i < 0) continue;
      for (const step of [-1, 1]) {{
        const zones = new Set();
        for (let j = i + step; j >= 0 && j < stops.length; j += step) {{
          zones.add(hopZone[stops[j - step] + '|' + stops[j]]);
          if (zones.size > MAX_ZONES) break;
          const prev = seen[stops[j]];
          if (!prev || prev.zones.size > zones.size) seen[stops[j]] = {{ zones: new Set(zones), hops: Math.abs(j - i), lines: new Set() }};
          seen[stops[j]].lines.add(line);
        }}
      }}
    }}
    return seen;
  }}

  const panelTitle = document.getElementById('panel-title');
  const panelIntro = document.getElementById('panel-intro');
  const reachList = document.getElementById('reach-list');
  const PANEL_TITLE = panelTitle.textContent, PANEL_INTRO = panelIntro.innerHTML;
  function fillPanel(origin, reach, n, zoneText) {{
    panelTitle.textContent = 'From ' + NET.stops[origin].name;
    panelIntro.innerHTML = '<strong>' + n + ' stops</strong> on a short journey ticket, reaching into fare ' + zoneText + '. Nearest first.';
    const items = Object.entries(reach).filter(([k]) => k !== origin)
      .sort((a, b) => a[1].hops - b[1].hops || NET.stops[a[0]].name.localeCompare(NET.stops[b[0]].name));
    reachList.innerHTML = items.map(([k, r]) => {{
      const dots = [...r.lines].sort().map(l => '<i style="background:' + NET.lineColours[l] + '" title="' + l + '"></i>').join('');
      const zs = NET.stops[k].zones;
      return '<li class="rl"><span class="rl-lines">' + dots + '</span><span class="rl-name">' + NET.stops[k].name + '</span>'
        + '<span class="rl-zone' + (zs.length > 1 ? ' two' : '') + '" title="Fare zone">' + zs.join(' / ') + '</span></li>';
    }}).join('');
  }}
  function resetPanel() {{
    panelTitle.textContent = PANEL_TITLE;
    panelIntro.innerHTML = PANEL_INTRO;
    reachList.innerHTML = '';
  }}

  let pinned = null, current = null;
  function show(origin) {{
    if (origin === current) return;
    current = origin;
    const reach = reachable(origin);
    const zonesUsed = new Set();
    Object.values(reach).forEach(s => s.zones.forEach(z => zonesUsed.add(z)));
    if (zonesUsed.size === 0) NET.stops[origin].zones.forEach(z => zonesUsed.add(z));
    svg.classList.add('active');
    for (const k in stnEls) {{
      const on = k in reach;
      stnEls[k].classList.toggle('reach', on);
      stnEls[k].classList.toggle('origin', k === origin);
      if (lblEls[k]) lblEls[k].classList.toggle('reach', on);
    }}
    tagEls.forEach(t => t.classList.toggle('reach', t.dataset.stop in reach));
    for (const z in zoneEls) zoneEls[z].forEach(el => el.classList.toggle('lit', zonesUsed.has(+z)));
    const n = Object.keys(reach).length - 1;
    const zl = [...zonesUsed].sort((a, b) => a - b);
    const zoneText = zl.length === 1 ? 'zone ' + zl[0] : 'zones ' + zl.slice(0, -1).join(', ') + ' and ' + zl[zl.length - 1];
    status.innerHTML = 'From <strong>' + NET.stops[origin].name + '</strong>: ' + n + ' stops are within a short journey on one tram, reaching into fare ' + zoneText + '.'
      + (pinned ? ' <button type="button" class="clear">Clear</button>' : '');
    fillPanel(origin, reach, n, zoneText);
  }}
  function clear() {{
    current = null;
    svg.classList.remove('active');
    svg.querySelectorAll('.reach, .origin, .lit').forEach(el => el.classList.remove('reach', 'origin', 'lit'));
    status.innerHTML = DEFAULT;
    resetPanel();
  }}
  function keyOf(target) {{
    const g = target.closest && target.closest('g.stn, g.lbl');
    return g ? g.dataset.name : null;
  }}

  svg.addEventListener('pointerover', e => {{
    if (e.pointerType !== 'mouse' || pinned) return;
    const k = keyOf(e.target);
    if (k) show(k);
  }});
  svg.addEventListener('pointerout', e => {{
    if (e.pointerType !== 'mouse' || pinned) return;
    const k = keyOf(e.target);
    if (k && keyOf(e.relatedTarget || document.body) !== k) clear();
  }});
  svg.addEventListener('click', e => {{
    const k = keyOf(e.target);
    if (k && k !== pinned) {{ pinned = k; current = null; show(k); }}
    else {{ pinned = null; clear(); }}
  }});
  svg.addEventListener('keydown', e => {{
    const k = keyOf(e.target);
    if (!k) return;
    if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); e.target.closest('g.stn').dispatchEvent(new MouseEvent('click', {{ bubbles: true }})); }}
    if (e.key === 'Escape') {{ pinned = null; clear(); }}
  }});
  svg.addEventListener('focusin', e => {{ const k = keyOf(e.target); if (k && !pinned) show(k); }});
  svg.addEventListener('focusout', e => {{ if (!pinned) clear(); }});
  status.addEventListener('click', e => {{ if (e.target.classList.contains('clear')) {{ pinned = null; clear(); }} }});
}})();
</script>
</body>
</html>
"""
open('/Users/andylulham/Documents/trammap/index.html', 'w').write(HTML)
print("wrote index.html", len(HTML))
