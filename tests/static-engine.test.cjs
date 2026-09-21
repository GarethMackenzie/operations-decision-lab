const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const engine = require('../src/decision_lab/static/static-engine.js');
const sample = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'decision_lab', 'samples', 'synthetic.csv'),
  'utf8',
);

const config = {
  arrival_rate: 18,
  max_workers: 4,
  pick_minutes: 6,
  pack_minutes: 7,
  service_cv: 0.5,
  shift_hours: 8,
  break_minutes: 0,
  sla_minutes: 60,
  initial_pick: 0,
  initial_pack: 0,
  baseline_pickers: 2,
  baseline_packers: 2,
  hourly_wage: 100,
  payroll_budget: 4800,
  target_fraction: 0.9,
  utilization_ceiling: 0.9,
  seed: 42,
};

test('static engine inspects the bundled sample', async () => {
  const quality = await engine.inspectCsv(
    sample,
    '2026-01-05T08:00:00+00:00',
    '2026-01-05T16:00:00+00:00',
  );
  assert.equal(quality.rows, 132);
  assert.equal(quality.arrivals_in_window, 132);
  assert.equal(quality.completions_in_window, 115);
  assert.equal(quality.sha256.length, 64);
  assert.ok(quality.warnings.length >= 3);
});

test('static engine runs and exports the default decision workflow', async () => {
  const response = await engine.compareRequest({
    csv: sample,
    window_start: '2026-01-05T08:00:00+00:00',
    window_end: '2026-01-05T16:00:00+00:00',
    config,
    assumptions_confirmed: true,
    active_service_confirmed: false,
    service_source: 'manual',
    data_origin: 'synthetic demo',
  });
  assert.equal(response.report.results.status, 'NO CONFIRMED FEASIBLE OPTION');
  assert.equal(response.report.results.scenarios.length, 6);
  assert.match(response.json, /"model_version": "0.1.0-web"/);
  assert.match(response.html, /Operations Decision Lab/);
  assert.match(response.downloads.json, /^blob:/);
  assert.match(response.downloads.html, /^blob:/);
  URL.revokeObjectURL(response.downloads.json);
  URL.revokeObjectURL(response.downloads.html);
});

test('static engine rejects malformed and unconfirmed inputs', async () => {
  await assert.rejects(
    () => engine.inspectCsv('wrong,headers\n1,2\n', '2026-01-05T08:00:00+00:00', '2026-01-05T16:00:00+00:00'),
    /unique headers/,
  );
  await assert.rejects(
    () => engine.makeReport({
      csv: sample,
      window_start: '2026-01-05T08:00:00+00:00',
      window_end: '2026-01-05T16:00:00+00:00',
      config,
      assumptions_confirmed: false,
      service_source: 'manual',
      data_origin: 'synthetic demo',
    }),
    /Confirm the hypothetical model assumptions/,
  );
});

test('static engine is deterministic and confirms a supported low-demand option', () => {
  const feasibleConfig = {
    ...config,
    arrival_rate: 4,
    pick_minutes: 3,
    pack_minutes: 3,
    max_workers: 4,
    target_fraction: 0.8,
    payroll_budget: 10000,
  };
  const first = engine.compare(feasibleConfig);
  const second = engine.compare(feasibleConfig);
  assert.equal(first.status, 'CONDITIONALLY FEASIBLE');
  assert.equal(first.confirmed_feasible, true);
  assert.deepEqual(first, second);
});
