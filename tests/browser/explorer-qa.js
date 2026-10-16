async (page, options = {}) => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const state=()=>page.evaluate(()=>window.__courtyard.getState());
  const check=(x,msg)=>{if(!x)throw new Error(msg);};
  const move=async(key,axis,target,direction,timeout=20000)=>{
    await page.keyboard.down(key);
    try{await page.waitForFunction(p=>{const x=window.__courtyard.getState().explorer.position[p.axis];return p.direction>0?x>=p.target:x<=p.target;},{axis,target,direction},{timeout});}
    finally{await page.keyboard.up(key);}
  };
  await page.reload();await page.waitForFunction(()=>window.__courtyard?.ready);
  const initial=await state();check(initial.explorer.enabled,'Third person not default');
  await page.screenshot({path:`${options.screenshotDir || 'tests/results/browser/screenshots'}/preview-walk.png`});
  await move('w',2,1.5,-1);const first=await state();check(first.explorer.area.includes('会客厅'),'Cannot enter first floor');check(first.explorer.position[1]>.95,'Character below floor');
  await page.screenshot({path:`${options.screenshotDir || 'tests/results/browser/screenshots'}/preview-room.png`});
  await move('a',0,-4.7,-1);
  await page.keyboard.down('a');await page.waitForTimeout(550);await page.keyboard.up('a');
  const wall=await state();check(wall.explorer.position[0]>-5.1,'Walked through wall');
  await move('s',2,3.01,1);await move('d',0,3.32,1);
  await move('w',2,-1.99,-1);const stairTop=await state();check(stairTop.explorer.level===1,'Stairs did not reach second floor');check(stairTop.explorer.position[1]>5.5,'Second floor height wrong');
  await move('a',0,1.7,-1);await move('s',2,1.6,1);const second=await state();check(second.explorer.area.includes('二层'),'Upper room not accessible');
  await page.screenshot({path:`${options.screenshotDir || 'tests/results/browser/screenshots'}/preview-upstairs.png`});
  await move('w',2,-1.99,-1);await move('d',0,3.32,1);await move('s',2,3.06,1);const downstairs=await state();check(downstairs.explorer.level===0&&!downstairs.explorer.onStairs,'Cannot descend stairs');
  await page.getByRole('button',{name:'↺ 重置',exact:true}).click();
  await page.keyboard.down('a');await page.waitForTimeout(1000);await page.keyboard.up('a');const pond=await state();check(pond.explorer.position[0]>-2.7,'Walked into pond');
  await page.getByRole('button',{name:'↺ 重置',exact:true}).click();await move('s',2,14.0,1);await move('a',0,-7.5,-1);await move('w',2,9,-1);const bridge=await state();check(bridge.explorer.area.includes('石拱桥')&&bridge.explorer.position[1]>1.15,'Bridge surface walking failed');
  await page.getByRole('button',{name:'鸟瞰',exact:true}).click();check(!(await state()).explorer.enabled,'Overview did not leave walking mode');
  await page.getByRole('button',{name:'♡ 少女漫游',exact:true}).click();check((await state()).explorer.enabled,'Cannot resume walking');
  await page.getByRole('button',{name:'↺ 重置',exact:true}).click();
  await page.setViewportSize({width:390,height:844});const forwardButton=await page.locator('[data-move="w"]').boundingBox();await page.mouse.move(forwardButton.x+forwardButton.width/2,forwardButton.y+forwardButton.height/2);await page.mouse.down();await page.waitForTimeout(500);await page.mouse.up();
  const mobile=await state();check(mobile.explorer.position[2]<11.3,'Touch movement failed');
  await page.screenshot({path:`${options.screenshotDir || 'tests/results/browser/screenshots'}/explorer-mobile.png`});
  await page.setViewportSize({width:1440,height:1000});await page.getByRole('button',{name:'↺ 重置',exact:true}).click();
  check(errors.length===0,'Runtime errors: '+errors.join(';'));
  return {passed:['third-person default','WASD movement','entry steps and doorway','interior wall collision','upstairs','downstairs','pond boundary','arched bridge height','overview toggle','touch controls'],first:first.explorer,second:second.explorer,downstairs:downstairs.explorer,bridge:bridge.explorer,wall:wall.explorer,errors};
}
