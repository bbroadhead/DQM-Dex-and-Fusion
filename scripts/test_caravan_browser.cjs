// DOM-level Caravan Heart smoke tests. Run with: npm install --no-save jsdom@26 && node scripts/test_caravan_browser.cjs
const fs=require("node:fs");
const path=require("node:path");
const assert=require("node:assert/strict");
const {JSDOM,VirtualConsole}=require("jsdom");
const root=path.resolve(__dirname,"..");
const errors=[];
const virtualConsole=new VirtualConsole();
virtualConsole.on("jsdomError",e=>errors.push(e.message));
virtualConsole.on("error",e=>errors.push(String(e)));
const html=fs.readFileSync(path.join(root,"index.html"),"utf8");
const dom=new JSDOM(html,{
  url:"https://example.test/",
  runScripts:"dangerously",
  virtualConsole,
  beforeParse(window){
    window.fetch=async url=>{
      const relative=String(url).split("?")[0];
      const file=path.resolve(root,relative);
      if(!file.startsWith(root+path.sep))throw Error("Unexpected path "+relative);
      if(!fs.existsSync(file))return {ok:false,status:404,json:async()=>({})};
      return {ok:true,status:200,json:async()=>JSON.parse(fs.readFileSync(file,"utf8"))};
    };
  }
});
const {document,Event}=dom.window;
const tick=()=>new Promise(resolve=>setTimeout(resolve,20));
async function waitFor(predicate,label){for(let i=0;i<100;i++){if(predicate())return;await tick();}throw Error("Timed out waiting for "+label)}
async function main(){
  await waitFor(()=>document.querySelector("[data-game=caravan]"),"game selector");
  const caravan=document.querySelector('[data-game="caravan"]');
  assert.ok(caravan,"Caravan Heart game button");
  caravan.click();
  await waitFor(()=>document.querySelectorAll(".monster-tile").length===221,"Caravan roster load");
  assert.ok(document.querySelector("#entries .monster-tile"),"Roster renders");
  assert.equal(document.querySelectorAll(".monster-tile").length,221,"Full roster count");
  assert.equal(document.querySelectorAll(".monster-tile .tag[title]").length,21,"Unobtainable badges");
  const toggle=document.querySelector("#showUnobtainable");
  assert.ok(toggle,"Unobtainable filter");
  toggle.checked=false;toggle.dispatchEvent(new Event("change",{bubbles:true}));
  assert.equal(document.querySelectorAll(".monster-tile").length,200,"Obtainable roster count");
  document.querySelector('[data-tab="fusion"]').click();
  await waitFor(()=>document.querySelector("#reformBase"),"Reform controls");
  const base=document.querySelector("#reformBase"),heart1=document.querySelector("#reformHeart1"),heart2=document.querySelector("#reformHeart2");
  assert.ok(base&&heart1&&heart2,"Reform controls render");
  for(const select of [base,heart1,heart2]){
    assert.equal(select.options.length,201,"200 obtainable options plus placeholder");
    assert.ok(![...select.options].some(o=>o.textContent.includes("Magarugi")),"Unobtainable excluded");
  }
  const choose=(el,value)=>{el.value=value;el.dispatchEvent(new Event("change",{bubbles:true}));};
  choose(base,"dqm3gba:slime");choose(heart1,"dqm3gba:slime");choose(heart2,"dqm3gba:slime");
  assert.match(document.querySelector("#reformResult").textContent,/Double-heart result: Slime/);
  choose(base,"dqm3gba:phoenix");choose(heart1,"dqm3gba:phoenix");choose(heart2,"dqm3gba:blizzardy");
  assert.match(document.querySelector("#reformResult").textContent,/Documented special result: Rain Hawk/);
  const chart=document.querySelector("#reformChartStars");
  choose(chart,"4");
  assert.match(document.querySelector("#reformChartTable").textContent,/Unresolved/);
  const target=document.querySelector("#reformTarget");
  choose(target,"dqm3gba:magarugi");
  assert.match(document.querySelector("#reformReverse").textContent,/Unobtainable/);
  assert.deepEqual(errors,[],"No browser JavaScript errors");
  console.log("Caravan Heart DOM smoke tests passed: roster, filter, selectors, double-heart, special recipe, chart, reverse lookup");
}
main().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>dom.window.close());
