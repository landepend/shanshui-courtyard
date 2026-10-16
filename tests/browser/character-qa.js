async (page, options = {}) => {
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.reload();
 await page.waitForFunction(()=>window.__courtyard?.getState().explorer.character.loaded);
 await page.setViewportSize({width:1440,height:1000});
 const state=()=>page.evaluate(()=>window.__courtyard.getState().explorer);
 const check=(v,m)=>{if(!v)throw new Error(m)};
 check((await state()).character.clip==='Idle','Idle missing');
 await page.keyboard.down('w');
 await page.waitForFunction(()=>window.__courtyard.getState().explorer.character.clip==='Walk');
 await page.waitForTimeout(400);const walk=await state();
 await page.keyboard.down('Shift');
 await page.waitForFunction(()=>window.__courtyard.getState().explorer.character.clip==='Run');
 const run=await state();await page.keyboard.up('Shift');await page.keyboard.up('w');
 await page.waitForFunction(()=>window.__courtyard.getState().explorer.character.clip==='Idle');
 await page.getByRole('button',{name:'↺ 重置',exact:true}).click();
 // Rotate the actual follow camera to inspect the face, then zoom in.
 await page.mouse.move(600,500);await page.mouse.down();
 await page.mouse.move(1385,500,{steps:20});await page.mouse.up();
 await page.mouse.wheel(0,-950);await page.waitForTimeout(900);
 await page.screenshot({path:`${options.screenshotDir || 'tests/results/browser/screenshots'}/atang-in-game.png`});
 check(errors.length===0,errors.join(';'));
 await page.getByRole('button',{name:'↺ 重置',exact:true}).click();
 return {passed:['GLB loaded','Idle','Walk','Run','stop to Idle','camera orbit and zoom'],walk:walk.character,run:run.character,errors};
}
