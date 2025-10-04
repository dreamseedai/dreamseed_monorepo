import { Router, Request, Response } from "express";
import crypto from "crypto";

const router = Router();
const STORE: Record<string, any> = {};

router.post("/", (req: Request, res: Response) => {
  const payload = req.body?.payload;
  if (!payload) return res.status(400).json({ error: "payload_required" });
  const id = crypto.randomBytes(6).toString("base64url"); // short id
  STORE[id] = payload;
  return res.json({ id, url: `/api/share/${id}` });
});

router.get("/:id", (req: Request, res: Response) => {
  const item = STORE[req.params.id];
  if (!item) return res.status(404).json({ error: "not_found" });
  return res.json(item);
});

export default router;
