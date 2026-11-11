// Show/Hide password (keeps the typed value)
document.querySelectorAll(".eye").forEach(b => b.addEventListener("click", () => {
  const i = document.getElementById(b.dataset.target);
  i.type = i.type === "password" ? "text" : "password";
  b.textContent = i.type === "password" ? "Show" : "Hide";
}));

// Live password rules (the server enforces the same rules)
const pw = document.getElementById("id_password1");
if (pw) {
  const tests = {
    len: p => p.length >= 8 && p.length <= 20,
    up: p => /^[A-Z]/.test(p),
    num: p => /\d/.test(p),
    sp: p => /[!@#$%&*^()_+\-=?.,:;]/.test(p),
  };
  pw.addEventListener("input", () => document.querySelectorAll("#rules li").forEach(li =>
    li.classList.toggle("ok", tests[li.dataset.r](pw.value))));
}

// Photo sliders on package cards
document.querySelectorAll(".slider").forEach(s => {
  const imgs = s.querySelectorAll("img"); let i = 0;
  const show = d => { i = (i + d + imgs.length) % imgs.length; imgs.forEach(m => m.style.transform = `translateX(-${i * 100}%)`); };
  s.querySelector(".l").onclick = e => { e.preventDefault(); show(-1); };
  s.querySelector(".r").onclick = e => { e.preventDefault(); show(1); };
});

// Booking total preview (server recalculates the real total)
const bf = document.getElementById("bookform");
if (bf) {
  const kind = bf.dataset.kind, unit = +bf.dataset.unit, extra = +bf.dataset.extra;
  const rooms = JSON.parse(bf.dataset.rooms || "{}");
  const val = n => bf.querySelector(`[name=${n}]`);
  const days = () => {
    const s = val("start_date"), e = val("end_date");
    if (!s || !e || !s.value || !e.value) return 1;
    const d = (new Date(e.value) - new Date(s.value)) / 864e5;
    return kind === "hotel" ? Math.max(d, 1) : Math.max(d + 1, 1);
  };
  const calc = () => {
    let t = 0;
    if (kind === "package") t = unit * (+val("members").value || 1) + extra;
    if (kind === "vehicle") t = unit * days();
    if (kind === "hotel") t = (+rooms[val("room").value] || 0) * days();
    document.getElementById("total").textContent = "₹" + t.toFixed(2);
  };
  bf.addEventListener("input", calc); calc();
}
