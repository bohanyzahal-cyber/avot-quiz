"""בונה את index.html מהתבנית + קובצי השאלות של היחידות.

הרצה:  python build.py      (מתוך התיקייה הזו)
כותב גם ל-avot-quiz/index.html וגם לעותק הנוח בתיקיית הקורס.

סכמת שאלה (קובץ לכל יחידה, uN.js, שורה לכל שאלה, בלי var ובלי סוגריים):
  {l:2,t:"נושא",s:"מקור",q:"השאלה",o:["א","ב","ג","ד"],c:1,e:"הסבר"},
  l = מספר היחידה, c = אינדקס התשובה הנכונה לפני הערבוב, s = "סיכום" / "מצגת" / "שאלות חזרה".
מבחן המוכנות (ready_uN.js) באותה סכמה, עם s:"מוכנות", מחוץ לבנק: הוא לא מופיע בתרגול
ובהדפסה, ולכן נבדק גם שאין בו שאלה שדומה לשאלה מהבנק.
"""
import os, sys, re, glob, json, subprocess, tempfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE   = os.path.dirname(os.path.abspath(__file__))
REPO   = os.path.dirname(HERE)                     # .../management-quiz
COURSE = os.path.dirname(REPO)                     # תיקיית הקורס

# (קובץ יעד, הקישור לדף הנגן של הפודקאסט) — כל קישור יחסי לתיקייה של הקובץ עצמו
TARGETS = [
    (os.path.join(REPO, "index.html"), "podcast/index.html"),
    (os.path.join(COURSE, "בוחן תרגול - מסכת אבות.html"), "avot-quiz/podcast/index.html"),
]

def unit_files(prefix):
    """מיון מספרי — מיון לקסיקוגרפי היה שם את u10 לפני u2.
    אות אחרי המספר מסמנת קובץ נוסף לאותה יחידה: u1z.js = שאלות ממפגש הזום, אחרי u1.js."""
    pat = re.compile(re.escape(prefix) + r"(\d+)([a-z]?)\.js")
    fs = [f for f in glob.glob(os.path.join(HERE, prefix + "*.js")) if pat.fullmatch(os.path.basename(f))]
    def key(f):
        m = pat.fullmatch(os.path.basename(f))
        return int(m.group(1)), m.group(2)
    return sorted(fs, key=key)

def bank_files():
    return unit_files("u")

def wrap(var, files):
    return "var %s=[\n" % var + "\n".join(open(f, encoding="utf-8").read().strip() for f in files) + "\n];"

tpl  = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
bank = wrap("BANK", bank_files())
ready_files = unit_files("ready_u")
ready = wrap("READY", ready_files) if ready_files else "var READY=[];"
exam5 = ""
full_bank = bank
mock = "var MOCK=[];"
mock2 = "var MOCK2=[];"
html = (tpl.replace("/*__BANK__*/", full_bank).replace("/*__READY__*/", ready)
        .replace("/*__MOCK__*/", mock + "\n" + mock2))

# קישור לפודקאסט — מוצג רק אם דף הנגן קיים
def aids_for(podcast_href):
    items = []
    if os.path.exists(os.path.join(REPO, "podcast", "index.html")):
        items.append('<a class="aid" href="' + podcast_href + '" target="_blank" rel="noopener">'
                     '<i>🎧</i><span><b>פודקאסט</b> · פרק לכל יחידה, עם שאלות לדרך — להאזנה בדרכים</span></a>')
    return ('<div class="aids">' + "".join(items) + "</div>") if items else ""

for t, podcast_href in TARGETS:
    open(t, "w", encoding="utf-8").write(html.replace("<!--AIDS-->", aids_for(podcast_href)))
    print("נכתב:", t)
html = html.replace("<!--AIDS-->", aids_for(TARGETS[0][1]))
print("גודל: %.0f KB" % (len(html) / 1024))

# ---------- סטטיסטיקה ----------
objs = re.findall(r'\{l:(\d+),t:"(.*?)",s:"(.*?)",q:', full_bank)
objs = [(int(l), t.replace('\\"', '"'), s.replace('\\"', '"')) for l, t, s in objs]
print("\nשאלות:", len(objs))

lects, topics, srcs = {}, {}, {}
for l, t, s in objs:
    lects[l]  = lects.get(l, 0) + 1
    topics[t] = topics.get(t, 0) + 1
    srcs[s]   = srcs.get(s, 0) + 1
print("\nלפי יחידה:")
for k in sorted(lects):
    print("  יחידה %-3d %3d" % (k, lects[k]))
print("לפי נושא:")
for k, v in sorted(topics.items(), key=lambda x: -x[1]):
    print("  %-34s %3d" % (k, v))
print("לפי מקור:")
for k, v in sorted(srcs.items(), key=lambda x: -x[1]):
    print("  %-16s %3d" % (k, v))
ready_l = [int(x) for x in re.findall(r'\{l:(\d+),t:"', ready)]
print("מבחן מוכנות: %d שאלות" % len(ready_l))
mock_l = [int(x) for x in re.findall(r'\{l:(\d+),t:"', mock)]
mock2_l = [int(x) for x in re.findall(r'\{l:(\d+),t:"', mock2)]
for label, js, ml in (("מבחן מדמה", mock, mock_l), ("מבחן מדמה ב'", mock2, mock2_l)):
    mc = re.findall(r',c:(\d),e:".*",fx:1\},\s*$', js, re.M)
    if ml:
        print("%s: %d שאלות · מפתח: %s" % (
            label, len(ml), " ".join("%s %d" % ("אבגדה"[i], mc.count(str(i))) for i in range(5))))
cs5 = re.findall(r',c:(\d),e:".*",fx:1\},\s*$', exam5, re.M)
n5 = len(cs5)
if n5:
    print("במבנה המבחן (חמש תשובות, סדר קבוע): %d שאלות · מפתח: %s" % (
        n5, " ".join("%s %d" % ("אבגדה"[i], cs5.count(str(i))) for i in range(5))))

cs = re.findall(r',c:(\d),e:"', bank)
dist = {}
for c in cs:
    dist[c] = dist.get(c, 0) + 1
print("\nפיזור אינדקס התשובה הנכונה במקור:", dict(sorted(dist.items())))
if len(cs) + n5 != len(objs):
    print("!! אזהרה: לא כל השאלות נותחו (%d מתוך %d)" % (len(cs) + n5, len(objs)))

# ---------- עדכון אוטומטי של ה-README ----------
def update_readme():
    path = os.path.join(REPO, "README.md")
    if not os.path.exists(path):
        return
    txt = open(path, encoding="utf-8").read()
    start, end = "<!-- STATS:START", "<!-- STATS:END -->"
    i, j = txt.find(start), txt.find(end)
    if i < 0 or j < 0:
        return
    LNAME = {1:"מבוא לתורה שבכתב ולתורה שבעל־פה",2:"מבוא למסכת אבות",3:"אנשי כנסת הגדולה",4:"שמעון הצדיק",
             5:"תקופת הזוגות והחשמונאים",6:"יהושע בן פרחיה",7:"שמעון בן שטח",8:"הלל הזקן",
             9:"מלחמת אחים וחורבן הבית",10:"אחרי החורבן — דור יבנה"}
    lines = ["| יחידה | נושא | שאלות |", "|---|---|---|"]
    for k in sorted(lects):
        lines.append("| %d | %s | %d |" % (k, LNAME.get(k, ""), lects[k]))
    src_line = " · ".join("%s (%d)" % (k, v) for k, v in sorted(srcs.items(), key=lambda x: -x[1]))
    if ready_l:
        src_line += "\n\n**מבחן מוכנות:** %d שאלות נוספות מיחידות %d–%d, מחוץ לבנק (לא מופיעות בתרגול ובהדפסה)" % (
            len(ready_l), min(ready_l), max(ready_l))
    for label, ml, more in (("מבחן מדמה א'", mock_l, ""),
                            ("מבחן מדמה ב'", mock2_l, ", ברמה גבוהה: תרחישים ארוכים והמושגים באנגלית")):
        if ml:
            src_line += ("\n\n**%s:** %d שאלות נוספות במבנה המבחן (חמש תשובות)%s, משיעורים %d–%d, "
                         "מחוץ לבנק; שעתיים, 5 נקודות לשאלה" % (label, len(ml), more, min(ml), max(ml)))
    top_line = " · ".join("%s (%d)" % (k, v) for k, v in topics.items())
    block = (
        "<!-- STATS:START — נוצר אוטומטית על ידי src/build.py, אין לערוך ידנית -->\n"
        "**%d שאלות** רב-ברירתיות (אמריקאיות): %d עם ארבע תשובות%s.\n\n"
        "%s\n\n"
        "**לפי מקור:** %s\n\n"
        "**נושאים:** %s\n"
        % (len(objs), len(objs) - n5,
           (", ו-%d במבנה המבחן של המרצה: חמש תשובות בסדר קבוע, כולל תשובות משולבות" % n5) if n5 else "",
           "\n".join(lines), src_line, top_line)
    )
    open(path, "w", encoding="utf-8").write(txt[:i] + block + txt[j:])
    print("עודכן:", path)

update_readme()

# ---------- בדיקות מבנה ----------
STRUCT = r"""
const fs=require('fs');
eval(fs.readFileSync(process.argv[2],'utf8'));
/* דפוסים תלויי-מיקום: האפליקציה מערבבת את סדר האפשרויות בכל סבב,
   ולכן מסיח כמו "כל התשובות נכונות" או "תשובות א'+ב'" נשבר. */
const POS=/כל התשובות נכונות|כל ההיגדים נכונים|כל הנ["״']ל|תשובות? א['׳']\s*(\+|ו)|א['׳']\s*(\+|ו-?)\s*ב['׳']|אף תשובה אינה|כל האמור לעיל|אף אחת מהתשובות|כל האפשרויות/;
const err=[], seen={};
BANK.forEach((q,i)=>{
  const at=`#${i} ${(q.q||'').slice(0,40)}`;
  if(typeof q.l!=='number'||q.l<1||q.l>13)  err.push(at+' — מספר שיעור חסר/שגוי');
  if(!q.t||!q.s||!q.q||!q.e)             err.push(at+' — שדה חסר');
  const N=q.fx?5:4;   /* fx = שאלה במבנה המבחן של המרצה: חמש תשובות בסדר קבוע */
  if(!Array.isArray(q.o)||q.o.length!==N) err.push(at+' — אין בדיוק '+N+' אפשרויות');
  else if(new Set(q.o).size!==N)          err.push(at+' — אפשרות כפולה');
  if(typeof q.c!=='number'||q.c<0||q.c>=N) err.push(at+' — c מחוץ לתחום');
  if(!q.fx&&(q.o||[]).some(o=>POS.test(o))) err.push(at+' — מסיח תלוי-מיקום');
  if(q.fx&&!/ נכונות$|אינה נכונה$/.test((q.o||[])[4]||'')) err.push(at+' — במבנה המבחן התשובה האחרונה משולבת או «אף אחת»');
  (q.o||[]).forEach((o)=>{
    const w=String(o).split(/\s+/);
    for(let k=0;k+1<w.length;k++){
      if(w[k].length>=4 && w[k]===w[k+1]) { err.push(at+' — מילה כפולה ברצף: "'+w[k]+'"'); break; }
      if(k+3<w.length && w[k].length>=4 && w[k]===w[k+3] && w[k+1]===w[k+4]) {
        err.push(at+' — ביטוי חוזר: "'+w.slice(k,k+2).join(' ')+'"'); break;
      }
    }
  });
  if((q.e||'').length<40)                 err.push(at+' — הסבר קצר מדי');
  if(seen[q.q]!==undefined)               err.push(at+' — שאלה כפולה (גם ב-#'+seen[q.q]+')');
  else seen[q.q]=i;
});

/* מפתח תשובה שגוי: c מצביע על מסיח בעוד ההסבר מתאר אפשרות אחרת.
   מדד רועש — לכן זו התראה לבדיקה ידנית ולא שגיאה. */
const STOP=new Set(('של את על אל כי גם רק אם לא זה זו אלה הוא היא הם הן אני אתה אנחנו יש אין כל כמו אבל או אז מה מי איך למה כאשר לאחר לפני בתוך בין עם ללא אשר היה היו יהיה להיות אינו אינה אינם מפני מכיוון בגלל כדי לכן ולכן אלא אף כך יותר פחות מאוד ממש בדרך כלל למשל דוגמה בהרצאה המרצה שהוא שהיא ניתן צריך יכול אפשר בפועל בלבד כמובן עדיין זאת אותו אותה אותם לפי השקף במצגת בשיעור').split(' '));
const stem=w=>w.replace(/^(כש|לכ|מה|שה|וה|וב|ול|ומ|ו|ה|ב|ל|מ|ש|כ)/,'');
const toks=s=>{const o=new Set();String(s).split(/[^\wא-ת]+/).forEach(w=>{
  if(w.length>=4 && !STOP.has(w)) o.add(stem(w));});return o;};
const key=[];
BANK.forEach((q,i)=>{
  if(!q.e||!Array.isArray(q.o)||q.fx) return;   /* בשאלות fx ההסבר עובר על כל המשפטים */
  const E=toks(q.e);
  const sc=q.o.map(o=>{const O=toks(o);let n=0;O.forEach(x=>{if(E.has(x))n++;});
                       return O.size? n/Math.sqrt(O.size):0;});
  const best=sc.indexOf(Math.max(...sc));
  if(best!==q.c && sc[best]-sc[q.c] > 1.5)
    key.push('#'+i+' מסומן '+q.c+' אך ההסבר מתאים ל-'+best+' — '+(q.q||'').slice(0,44));
});
console.log(JSON.stringify({n:BANK.length,err,key}));
"""

try:
    with tempfile.TemporaryDirectory() as td:
        jsf = os.path.join(td, "all.js")
        open(jsf, "w", encoding="utf-8").write(full_bank)
        chk = os.path.join(td, "struct.js")
        open(chk, "w", encoding="utf-8").write(STRUCT)
        r = subprocess.run(["node", chk, jsf], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "")[:300])
        s = json.loads(r.stdout.strip())
        print("\nבדיקות מבנה (%d שאלות):" % s["n"])
        if s["err"]:
            for e in s["err"][:40]:
                print("  !!", e)
            if len(s["err"]) > 40:
                print("  ... ועוד %d" % (len(s["err"]) - 40))
        else:
            print("  תקין — ללא כפילויות, שדות חסרים או מסיחים תלויי-מיקום.")
        for k in s.get("key", []):
            print("  !! מפתח תשובה:", k)
        if ready_l:
            open(jsf, "w", encoding="utf-8").write(ready.replace("var READY", "var BANK", 1))
            r = subprocess.run(["node", chk, jsf], capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                raise RuntimeError((r.stderr or "")[:300])
            s = json.loads(r.stdout.strip())
            print("\nבדיקות מבנה — מבחן מוכנות (%d שאלות):" % s["n"])
            for e in s["err"]:
                print("  !!", e)
            for k in s.get("key", []):
                print("  !! מפתח תשובה:", k)
            if not s["err"]:
                print("  תקין.")
        for label, js, var, ml in (("מבחן מדמה", mock, "var MOCK", mock_l), ("מבחן מדמה ב'", mock2, "var MOCK2", mock2_l)):
            if not ml:
                continue
            open(jsf, "w", encoding="utf-8").write(js.replace(var, "var BANK", 1))
            r = subprocess.run(["node", chk, jsf], capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                raise RuntimeError((r.stderr or "")[:300])
            s = json.loads(r.stdout.strip())
            print("\nבדיקות מבנה — %s (%d שאלות):" % (label, s["n"]))
            for e in s["err"]:
                print("  !!", e)
            if not s["err"]:
                print("  תקין.")
except Exception as e:
    print("\n(בדיקות המבנה דילגו — נדרש node:", e, ")")

# ---------- מבחן המוכנות לא חוזר על שאלות מהבנק ----------
# אם שאלה במבחן המוכנות דומה לשאלה שכבר תורגלה, הציון שוב מודד זיכרון ולא שליטה בחומר.
def stems(js):
    return [x.replace('\\"', '"') for x in re.findall(r'q:"((?:[^"\\]|\\.)*)"', js)]

def words(t):
    out = set()
    for w in re.findall(r"[\wא-ת']+", t):
        w = re.sub(r"^(וכש|כש|וה|וב|ול|ומ|ה|ב|ל|מ|ש|ו|כ)(?=[א-ת]{3})", "", w)
        if len(w) >= 3:
            out.add(w)
    return out

def stems_opts(js):
    """גוף השאלה יחד עם התשובות. בשאלות במבנה של המרצה גוף השאלה קצר וגנרי («מה נכון לגבי...»),
    ולכן משווים אותן לפי כל הטקסט, ולא לפי גוף השאלה לבדו."""
    out = []
    for q, o in re.findall(r'q:"((?:[^"\\]|\\.)*)",o:\[((?:[^\]"\\]|"(?:[^"\\]|\\.)*")*)\]', js):
        out.append((q + " " + " ".join(re.findall(r'"((?:[^"\\]|\\.)*)"', o))).replace('\\"', '"'))
    return out

for label, extra_js, get, ref_js in (("מבחן מוכנות מול הבנק", ready if ready_l else "", stems, full_bank),
                                     ("מבחן מדמה מול הבנק", mock if mock_l else "", stems_opts, full_bank),
                                     ("מבחן מדמה ב' מול הבנק ומול טופס א'", mock2 if mock2_l else "", stems_opts,
                                      full_bank + "\n" + mock)):
    if not extra_js:
        continue
    bank_stems = [(x, words(x)) for x in get(ref_js)]
    close = []
    for rq in get(extra_js):
        rw = words(rq)
        best, bq = 0.0, ""
        for bq_, bw in bank_stems:
            if not rw or not bw:
                continue
            j = len(rw & bw) / len(rw | bw)
            if j > best:
                best, bq = j, bq_
        if best >= 0.45:
            close.append((best, rq, bq))
    print("\n%s:" % label)
    if close:
        for j, rq, bq in sorted(close, reverse=True):
            print("  !! דומה (%.2f): %s\n       שם: %s" % (j, rq[:70], bq[:70]))
    else:
        print("  תקין — אין שאלה שדומה לשאלה קיימת.")

# ---------- בדיקת "תל האורך" ----------
# כשכותבים שאלות בכמות, התשובה הנכונה יוצאת כמעט תמיד הארוכה ביותר,
# ואז אפשר לענות נכון בלי לקרוא. זו בדיקה שהבעיה לא חזרה.
CHECK = r"""
const fs=require('fs');
eval(fs.readFileSync(process.argv[2],'utf8'));
const n=BANK.length, rank=[0,0,0,0];
let long=0, short=0, outlierHit=0;
const outliers=[];
BANK.forEach((q,qi)=>{
  const L=q.o.map(o=>o.length), max=Math.max(...L), min=Math.min(...L);
  if(L.indexOf(max)===q.c) long++;
  if(L.indexOf(min)===q.c) short++;
  rank[L.map((l,i)=>[l,i]).sort((a,b)=>b[0]-a[0]).map(x=>x[1]).indexOf(q.c)]++;
  const d=L.filter((_,i)=>i!==q.c), avg=d.reduce((a,b)=>a+b,0)/d.length;
  const gap=(L[q.c]-avg)/avg;
  if(Math.abs(gap)>=0.40) outliers.push({i:qi,q:q.q.slice(0,42),pct:Math.round(gap*100)});
  const mean=L.reduce((a,b)=>a+b,0)/4;
  const far=L.map((l,i)=>[Math.abs(l-mean),i]).sort((a,b)=>b[0]-a[0])[0][1];
  if(far===q.c) outlierHit++;
});
console.log(JSON.stringify({n,long,short,rank,outliers,outlierHit}));
"""
def length_stats(js_text, td, tag):
    jsf = os.path.join(td, "b_%s.js" % tag)
    prefix = "" if js_text.lstrip().startswith("var BANK") else "var BANK=[];\n"
    open(jsf, "w", encoding="utf-8").write(prefix + js_text)
    chk = os.path.join(td, "check.js")
    if not os.path.exists(chk):
        open(chk, "w", encoding="utf-8").write(CHECK)
    r = subprocess.run(["node", chk, jsf], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "")[:200])
    return json.loads(r.stdout.strip())

def report(s, label, indent="  "):
    n = s["n"]
    if not n:
        return False
    pct = lambda x: int(round(x / n * 100))
    flag = "  <-- !!" if max(pct(s["long"]), pct(s["short"])) > 45 else ""
    print("%s%-14s n=%-4d ארוכה=%3d%%  קצרה=%3d%%  (פיזור %s)%s"
          % (indent, label, n, pct(s["long"]), pct(s["short"]),
             "/".join("%d" % pct(x) for x in s["rank"]), flag))
    return bool(flag)

try:
    with tempfile.TemporaryDirectory() as td:
        print("\nבדיקת אורך התשובות (כדי שלא ניתן יהיה לענות בלי לקרוא) — [מקרי ≈ 25%, אחיד = 25/25/25/25]:")
        bad_files = []
        for f in bank_files():
            name = os.path.basename(f)
            txt = wrap("BANK", [f])
            if report(length_stats(txt, td, name), name):
                bad_files.append(name)
        if ready_l:
            if report(length_stats(ready.replace("var READY", "var BANK", 1), td, "ready"), "ready_u*.js"):
                bad_files.append("ready_u*.js")
        print("  " + "-" * 58)
        all_stats = length_stats(bank, td, "all")
        report(all_stats, "סה\"כ")
        out = all_stats.get("outliers", [])
        n_all = all_stats["n"]
        hit = all_stats.get("outlierHit", 0)
        pct_hit = int(round(hit / n_all * 100)) if n_all else 0
        longish = sum(1 for o in out if o["pct"] > 0)
        print("\n  חריגות אורך (פער מממוצע המסיחים, לא דירוג):")
        print("    %d שאלות חורגות ב-40%% ומעלה — %d ארוכות מדי, %d קצרות מדי"
              % (len(out), longish, len(out) - longish))
        print("    אסטרטגיית \"בחר את החורגת ביותר\": %d%%%s"
              % (pct_hit, "   <-- !!" if pct_hit > 45 else "   (מקרי 25%)"))
        if "--outliers" in sys.argv:
            for o in out:
                print("      #%d %+d%%  %s" % (o["i"], o["pct"], o["q"]))
        if bad_files:
            print("  !! חריגה ב:", ", ".join(bad_files),
                  "— אפשר לצבור שם מעל 45% בלי לקרוא. הארך (או קצר) מסיחים בקובץ החורג.")
        else:
            print("  תקין — אף אסטרטגיה עיוורת אינה עוברת 45% באף קובץ.")
except Exception as e:
    print("\n(בדיקת האורך דילגה — נדרש node:", e, ")")
