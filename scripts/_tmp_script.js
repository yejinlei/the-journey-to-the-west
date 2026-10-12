document.addEventListener('DOMContentLoaded', function () {
  const params = new URLSearchParams(window.location.search);

  const getParam = (key) => {
    const val = params.get(key);
    return val ? val.trim() : '';
  };

  // 文件名
  const fname = getParam('n') || getParam('t');
  if (fname) {
    document.title = '请选择网盘下载：' + fname;
    document.getElementById('file-name-display').textContent = fname;
  }

  const data = {
    yun: getParam('yun'),
    hjhb: getParam('hj'),
    aliyp: getParam('ay'),
    bdpan: getParam('bd'),
    dou: getParam('dou'),
    df: getParam('df'),
    bw: getParam('hb'),
    rs: getParam('rs') || 'rs',
    durl: getParam('d') || getParam('y'),
    md5: getParam('m'),
    ages: getParam('a'),
    sj: getParam('sj'),
    sjd: getParam('sjd'),
  };

  // ---------- 左栏：轻量文档 ----------
  let lightHasContent = false;

  // 第一排：sj -> 书格存储二维码
  if (data.sj) {
    const sjUrl = 'https://du.shuge.org/@s/' + data.sj;
    document.getElementById('row-qr').style.display = 'block';
    document.getElementById('qr-link').href = sjUrl;
    // 根据屏幕宽度自适应二维码尺寸，小屏更紧凑
    const qrSize = Math.max(120, Math.min(150, Math.round(window.innerWidth * 0.38)));
    // eslint-disable-next-line no-undef
    new QRCode(document.getElementById('qrcode'), {
      text: sjUrl,
      width: qrSize,
      height: qrSize,
      colorDark: '#333333',
      colorLight: '#ffffff',
    });
    lightHasContent = true;
  }

  // 第二排：sjd -> 豆包云盘按钮
  if (data.sjd) {
    const sjdUrl = 'https://feishu.doubao.com/drive/file/' + data.sjd;
    const btn = document.getElementById('btn-sjd');
    btn.href = sjdUrl;
    document.getElementById('row-btn').style.display = 'block';
    lightHasContent = true;
  }

  // 第三排：黑白版
  let bwUrl = '';
  if (data.bw) {
    bwUrl = 'https://bw.shuge.org/@s/' + data.bw;
    if (data.bw.length > 40) {
      bwUrl = 'https://shuge-my.sharepoint.com/personal/wei_shuge_onmicrosoft_com/_layouts/52/download.aspx?share=' + data.bw;
    }
    document.getElementById('bw-link').href = bwUrl;
    document.getElementById('row-bw').style.display = 'block';
    lightHasContent = true;
  }

  if (!lightHasContent) {
    document.getElementById('light-empty-tip').style.display = 'block';
  }

  // 轻量文档说明气泡交互
  const infoBtn = document.getElementById('light-info-btn');
  const infoBubble = document.getElementById('light-info-bubble');
  if (infoBtn && infoBubble) {
    infoBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      const isOpen = infoBubble.classList.toggle('open');
      infoBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    document.addEventListener('click', function (e) {
      if (!infoBubble.contains(e.target) && e.target !== infoBtn) {
        if (infoBubble.classList.contains('open')) {
          infoBubble.classList.remove('open');
          infoBtn.setAttribute('aria-expanded', 'false');
        }
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && infoBubble.classList.contains('open')) {
        infoBubble.classList.remove('open');
        infoBtn.setAttribute('aria-expanded', 'false');
        infoBtn.focus();
      }
    });
  }

  // ---------- 右栏：原始文档（原色版）----------
  const toneMap = {
    '#f05858': 'zhusha',
    '#446dff': 'dianlan',
    '#11b8ff': 'piaobi',
    '#24f6f0': 'zhuqing',
    zhusha: 'zhusha',
    dianlan: 'dianlan',
    piaobi: 'piaobi',
    zhuqing: 'zhuqing',
    daizi: 'daizi',
    mohui: 'mohui',
    shuge: 'zhusha',
    alipan: 'dianlan',
    baidu: 'piaobi',
    doubao: 'zhuqing',
  };

  const brandByTone = {
    zhusha: 'shuge',
    dianlan: 'alipan',
    piaobi: 'baidu',
    zhuqing: 'doubao',
  };

  const createLi = (href, toneOrColor, ...rest) => {
    let title = '';
    let subtitle = '';
    let desc = '';
    if (rest.length >= 4) {
      // 兼容 createLi(url, color, icon, title, subtitle, desc) 6参格式
      [, title, subtitle, desc] = rest;
    } else {
      // 兼容 createLi(url, colorOrTone, title, subtitle, desc) 5参格式
      [title, subtitle, desc] = rest;
    }
    const tone = toneMap[toneOrColor] || toneOrColor;
    const brand = brandByTone[tone];
    return `
      <li>
        <a href="${href}" title="${title}" target="_blank" class="download-card tone-${tone}">
          ${brand ? `<span class="brand-mark brand-${brand}" aria-hidden="true"></span>` : ''}
          <div class="card-inner">
            <h4>${title}</h4>
            <h6>${subtitle}</h6>
            <p>${desc}</p>
          </div>
        </a>
      </li>`;
  };

  let gridHtml = '';
  let originalCount = 0;

  // 书格存储 (Yun)
  if (data.yun) {
    gridHtml += createLi('https://yun.shuge.org/@s/' + data.yun, '#f05858', '', '书格存储', '全球推荐', '建议使用支持断点续传的软件下载');
    originalCount++;
  }

  // 书格存储 (Hjhb)
  if (data.hjhb) {
    gridHtml += createLi('https://shuge.hanjihebi.com/@s/' + data.hjhb, '#f05858', '', '书格存储', '全球推荐', '建议使用支持断点续传的软件下载');
    originalCount++;
  }

  // 阿里云盘
  if (data.aliyp) {
    gridHtml += createLi('https://www.alipan.com/s/' + data.aliyp, '#446dff', '', '阿里云盘', '中国推荐', '阿里旗下免费产品，支持转存和不限速下载（需注册会员）');
    originalCount++;
  }

  // 百度网盘
  if (data.bdpan) {
    gridHtml += createLi('https://pan.baidu.com/s/' + data.bdpan + '?pwd=6666', '#11b8ff', '', '百度网盘', '中国推荐', '百度旗下产品，支持转存下载（需注册会员）');
    originalCount++;
  }

  // 豆包云盘
  if (data.dou) {
    // 根据 df 参数的值判断使用哪种链接格式
    const douUrl = data.df === '1'
      ? 'https://feishu.doubao.com/drive/shr/' + data.dou
      : 'https://feishu.doubao.com/drive/file/' + data.dou;
    gridHtml += createLi(douUrl, '#24f6f0', '', '豆包云盘', '中国推荐', '字节跳动旗下产品，支持转存下载（免登录）');
    originalCount++;
  }

  // 全站同步 (Resilio Sync)
  if (data.rs) {
    gridHtml += createLi('https://s.shuge.org/' + data.rs, 'daizi', '全站同步', '全球推荐', '加入到 Resilio Sync 共享计划');
    originalCount++;
  }

  document.getElementById('download-grid').innerHTML = gridHtml;

  if (originalCount <= 1) {
    document.getElementById('link-fail-msg').style.display = 'block';
  }

  // ---------- 底部信息 ----------
  if (data.ages) {
    document.getElementById('age-val').textContent = data.ages;
    document.getElementById('age-warning').style.display = 'block';
  }

  if (data.durl) {
    const fullShortUrl = 'https://s.shuge.org/' + data.durl;
    document.getElementById('short-url-val').textContent = fullShortUrl;
    document.getElementById('short-url-container').style.display = 'block';

    const copyBtn = document.getElementById('copy-short-url-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', function () {
        const urlText = document.getElementById('short-url-val').textContent || fullShortUrl;
        if (!urlText) return;

        const setCopied = () => {
          copyBtn.textContent = '已复制';
          copyBtn.classList.add('copied');
          setTimeout(() => {
            copyBtn.textContent = '复制';
            copyBtn.classList.remove('copied');
          }, 1800);
        };

        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(urlText).then(setCopied).catch(() => fallbackCopy(urlText));
        } else {
          fallbackCopy(urlText);
        }

        function fallbackCopy(text) {
          const textarea = document.createElement('textarea');
          textarea.value = text;
          textarea.style.position = 'fixed';
          textarea.style.top = '0';
          textarea.style.left = '0';
          textarea.style.opacity = '0';
          document.body.appendChild(textarea);
          textarea.focus();
          textarea.select();
          try {
            document.execCommand('copy');
            setCopied();
          } catch (e) {
            copyBtn.textContent = '复制失败';
            setTimeout(() => {
              copyBtn.textContent = '复制';
            }, 1800);
          }
          document.body.removeChild(textarea);
        }
      });
    }

    // 短链二维码弹窗（首次打开时才生成二维码）
    const qrBtn = document.getElementById('qr-short-url-btn');
    const qrDialog = document.getElementById('short-qr-dialog');
    if (qrBtn && qrDialog) {
      let qrRendered = false;
      qrBtn.addEventListener('click', function () {
        if (!qrRendered) {
          // eslint-disable-next-line no-undef
          new QRCode(document.getElementById('short-qrcode'), {
            text: fullShortUrl,
            width: 200,
            height: 200,
            colorDark: '#333333',
            colorLight: '#ffffff',
          });
          document.getElementById('short-qr-url').textContent = fullShortUrl;
          qrRendered = true;
        }
        if (typeof qrDialog.showModal === 'function') {
          qrDialog.showModal();
        } else {
          qrDialog.setAttribute('open', '');
        }
      });

      const closeDialog = () => {
        if (typeof qrDialog.close === 'function') qrDialog.close();
        else qrDialog.removeAttribute('open');
      };
      document.getElementById('short-qr-close').addEventListener('click', closeDialog);
      // 点击遮罩区域关闭
      qrDialog.addEventListener('click', function (e) {
        if (e.target === qrDialog) closeDialog();
      });
    }
  }

  if (data.md5) {
    document.getElementById('md5-val').textContent = data.md5;
    document.getElementById('md5-container').style.display = 'block';
  }
});
