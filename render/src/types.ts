import {z} from 'zod';

export const captionWord = z.object({
  word: z.string(),
  start: z.number(),
  end: z.number(),
});

export const visual = z.object({
  type: z.enum(['stock_video', 'image', 'veo']),
  url: z.string().optional(),
  key: z.string().optional(),
  query: z.string().optional(),
});

export const shortSchema = z.object({
  video_id: z.number().default(0),
  duration: z.number().default(30),
  audio_url: z.string().nullable().default(null),
  captions: z.array(captionWord).default([]),
  visuals: z.array(visual).default([]),
  hook: z.string().nullable().default(null),
});

export type ShortProps = z.infer<typeof shortSchema>;
export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
