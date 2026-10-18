/** Read-only MCP tool server. No arbitrary file paths or shell tool execution. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

type Sample = {
  sample_id: string; material: string; family: string;
  conductivity_s_cm: number; temperature_c: number;
};

function csvRows(): Sample[] {
  // A fixed file configured by the server operator, not the LLM/user.
  const pathname = resolve(process.env.SCIW_EXPERIMENTS_CSV || 'data/experiments_demo.csv');
  const lines = readFileSync(pathname, 'utf8').trim().split(/\r?\n/);
  const header = lines.shift()?.split(',') ?? [];
  for (const name of ['sample_id', 'material', 'family', 'conductivity_s_cm', 'temperature_c']) {
    if (!header.includes(name)) throw Error(`Missing CSV column: ${name}`);
  }
  return lines.map((line, index) => {
    // The demo CSV format deliberately excludes quoted commas/newlines; production needs a CSV parser.
    const fields = line.split(',');
    if (fields.length !== header.length) throw Error(`Malformed CSV row: ${index + 2}`);
    const obj = Object.fromEntries(header.map((h, i) => [h, fields[i]]));
    const conductivity = Number(obj.conductivity_s_cm);
    const temperature = Number(obj.temperature_c);
    if (![conductivity, temperature].every(Number.isFinite) || conductivity < 0) {
      throw Error(`Invalid numeric values in CSV row: ${index + 2}`);
    }
    return { sample_id: obj.sample_id, material: obj.material, family: obj.family,
      conductivity_s_cm: conductivity, temperature_c: temperature };
  });
}

serveStdio(() => {
  const server = new McpServer({ name: 'sciwork-lab-tools', version: '0.1.0' });
  server.registerTool('analyze_experiments', {
    description: 'Read a fixed synthetic conductivity CSV, filter and order measurements; read-only.',
    inputSchema: z.object({ min_conductivity: z.number().finite().nonnegative().default(0) }),
  }, async ({ min_conductivity }) => {
    const samples = csvRows().filter(s => s.conductivity_s_cm >= min_conductivity)
      .sort((a, b) => b.conductivity_s_cm - a.conductivity_s_cm || a.sample_id.localeCompare(b.sample_id));
    const temperatures = [...new Set(samples.map(s => s.temperature_c))].sort((a, b) => a - b);
    const data = { total_matching: samples.length, threshold_s_cm: min_conductivity,
      samples, temperature_values_c: temperatures, comparable_temperatures: temperatures.length <= 1,
      data_provenance: 'synthetic CSV demo; not laboratory observations' };
    return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
  });
  return server;
});
