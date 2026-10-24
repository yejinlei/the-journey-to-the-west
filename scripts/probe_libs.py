import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

sites = [
    # 日本
    "kokusho.nijl.ac.jp",
    "rmda.kulib.kyoto-u.ac.jp",
    "da.dl.itc.u-tokyo.ac.jp",
    "dcollections.lib.keio.ac.jp",
    "db2.sido.keio.ac.jp",
    "kanji.zinbun.kyoto-u.ac.jp",
    "ycu.repo.nii.ac.jp",
    "www.digital.archives.go.jp",
    "emuseum.nich.go.jp",
    "dl.ndl.go.jp",
    # 欧美
    "digicoll.lib.berkeley.edu",
    "dpul.princeton.edu",
    "artmuseum.princeton.edu",
    "open.library.ubc.ca",
    "digital.bodleian.ox.ac.uk",
    "digital.staatsbibliothek-berlin.de",
    "gallica.bnf.fr",
    "idp.bl.uk",
    "www.britishmuseum.org",
    "search.rsl.ru",
    "www.clevelandart.org",
    # 港澳台
    "digitalarchive.npm.gov.tw",
    "rarebooks-maps.npm.edu.tw",
    "digitalrepository.lib.hku.hk",
    "repository.lib.cuhk.edu.hk",
    # 大陆
    "guji.nlc.cn",
    "guji.cckb.cn",
    "lib.hytc.edu.cn",
    "www.dpm.org.cn",
    "www.guoxuedashi.net",
    "old.shuge.org",
    "f.shuge.org",
]

for s in sites:
    try:
        req = urllib.request.Request("https://" + s + "/", headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=10)
        print("OK  ", s, r.status)
    except Exception as e:
        msg = str(e)
        if len(msg) > 50:
            msg = msg[:50]
        print("FAIL", s, type(e).__name__, msg)
