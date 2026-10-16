async (page, options = {}) => {
  await page.waitForFunction(()=>window.__courtyard?.ready);
  const initial=await page.evaluate(()=>window.__courtyard.getState().explorer.position[2]);
  await page.keyboard.down('w');
  try{await page.waitForFunction(z=>window.__courtyard.getState().explorer.position[2]<z-.7,initial,{timeout:4000});}
  finally{await page.keyboard.up('w');}
  await page.getByRole('button',{name:'☾ 夜景',exact:true}).click();
  if(await page.evaluate(()=>window.__courtyard.getState().mode)!=='night')throw new Error('Single-file mode failed');
  return {singleFile:true,ready:true,movement:true,night:true};
}
