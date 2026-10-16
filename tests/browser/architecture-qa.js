async (page, options = {}) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const state = () => page.evaluate(() => window.__courtyard.getState());
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  await page.reload();
  await page.waitForFunction(() => window.__courtyard?.getState().architecture.loaded, null, { timeout: 90000 });
  await page.setViewportSize({ width: 1440, height: 1000 });
  const initial = await state();
  const architecture = initial.architecture;
  check(architecture.source === 'Blender GLB' && architecture.loaded && !architecture.error, 'Blender building did not load');
  check(architecture.meshes > 5 && architecture.triangles > 10000, 'Building geometry missing');
  for (const part of ['roof', 'dougong', 'column', 'window', 'corridor']) check(architecture.parts[part] > 0, 'Missing selectable ' + part);
  check(architecture.bounds.min[0] < -15 && architecture.bounds.max[0] > 15 && architecture.bounds.max[1] > 10, 'Architecture scale or axes are incorrect');
  check(await page.locator('#architecture-status').count() === 0, 'Loading status remained after successful load');

  await page.locator('[data-view="front"]').click();
  await page.waitForFunction(() => Math.abs(window.__courtyard.getState().camera[0]) < .03);
  await page.screenshot({ path: `${options.screenshotDir || 'tests/results/browser/screenshots'}/architecture-front.png` });
  await page.locator('[data-mode="day"]').click();
  check((await state()).mode === 'day', 'Daylight control failed');
  const dayGlow = (await state()).architecture.windowGlow;
  await page.locator('[data-mode="night"]').click();
  const night = await state();
  check(night.mode === 'night' && night.architecture.windowGlow > dayGlow, 'Architecture night lighting did not update');
  check(night.architecture.windowLightMaterials > 0, 'No window paper material responded to night lighting');
  await page.screenshot({ path: `${options.screenshotDir || 'tests/results/browser/screenshots'}/architecture-night.png` });
  await page.locator('[data-mode="dusk"]').click();
  await page.locator('#reset').click();
  await page.waitForFunction(() => Math.abs(window.__courtyard.getState().camera[0] - 24) < .03);
  const point = await page.evaluate(() => window.__courtyard.screenPoint('column'));
  await page.mouse.click(point.x, point.y);
  check((await state()).selected === 'column', 'Real geometry raycast did not select the front column');
  await page.locator('#close-info').click();
  await page.locator('[data-view="bird"]').click();
  await page.waitForFunction(() => Math.abs(window.__courtyard.getState().camera[1] - 40) < .03);
  await page.screenshot({ path: `${options.screenshotDir || 'tests/results/browser/screenshots'}/architecture-bird.png` });

  // A missing GLB must be visible to the player; no procedural fallback may impersonate it.
  await page.route('**/assets/architecture/courtyard.glb', route => route.abort('failed'));
  await page.reload();
  await page.waitForFunction(() => Boolean(window.__courtyard?.getState().architecture.error));
  const failed = await state();
  check(!failed.architecture.loaded && failed.architecture.meshes === 0, 'Missing GLB silently fell back to old architecture');
  check(await page.locator('#architecture-status[role="alert"]').isVisible(), 'Load error was not visibly reported');
  await page.screenshot({ path: `${options.screenshotDir || 'tests/results/browser/screenshots'}/architecture-load-error.png` });
  await page.unroute('**/assets/architecture/courtyard.glb');
  await page.reload();
  await page.waitForFunction(() => window.__courtyard?.getState().architecture.loaded, null, { timeout: 90000 });
  check(errors.length === 0, 'Unexpected page errors: ' + errors.join('; '));
  return {
    passed: ['local Blender GLB', 'world-coordinate dimensions', 'all five component categories', 'day and night window lighting', 'actual column raycast', 'front and bird views', 'explicit load-failure notice', 'recovery after reload'],
    architecture, nightGlow: night.architecture.windowGlow,
    failureNotice: failed.architecture.error, final: await state(), errors
  };
}
