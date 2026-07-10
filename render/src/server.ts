import express from 'express';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const app = express();
app.use(express.json({limit: '25mb'}));

const PORT = Number(process.env.PORT ?? 3001);
const ENTRY = path.join(process.cwd(), 'src', 'index.ts');

// Bundle once and reuse the serve URL across renders.
let bundlePromise: Promise<string> | null = null;
function getBundle(): Promise<string> {
  if (!bundlePromise) {
    bundlePromise = bundle({entryPoint: ENTRY});
  }
  return bundlePromise;
}

app.get('/health', (_req, res) => {
  res.json({status: 'ok'});
});

app.post('/render', async (req, res) => {
  const inputProps = req.body ?? {};
  try {
    const serveUrl = await getBundle();
    const composition = await selectComposition({
      serveUrl,
      id: 'Short',
      inputProps,
    });

    const outPath = path.join(
      os.tmpdir(),
      `short-${inputProps.video_id ?? Date.now()}.mp4`
    );

    await renderMedia({
      composition,
      serveUrl,
      codec: 'h264',
      outputLocation: outPath,
      inputProps,
      chromiumOptions: {gl: 'angle'},
    });

    const buffer = fs.readFileSync(outPath);
    fs.unlink(outPath, () => undefined);
    res.setHeader('Content-Type', 'video/mp4');
    res.send(buffer);
  } catch (err) {
    console.error('render failed', err);
    res.status(500).json({error: String(err)});
  }
});

app.listen(PORT, () => {
  console.log(`AutoTube render service listening on :${PORT}`);
});
