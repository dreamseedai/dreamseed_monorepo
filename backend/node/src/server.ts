import express from "express";
import cors from "cors";
import diagnosticsRouter from "./routes/diagnostics";
import shareRouter from "./routes/share";

const app = express();

// Middleware
app.use(cors({
  origin: [
    "https://dreamseedai.com",
    "https://staging.dreamseedai.com", 
    "http://localhost:5173",
    "http://localhost:3000"
  ],
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["*"],
  maxAge: 600
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use("/api/diagnostics", diagnosticsRouter);
app.use("/api/share", shareRouter);

// Health check
app.get("/", (req, res) => {
  res.json({ message: "DreamSeedAI API is running" });
});

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "dreamseed-api" });
});

// Profile routes (demo)
app.get("/api/profile/:userId", (req, res) => {
  const { userId } = req.params;
  res.json({
    userId,
    country: "US",
    grade: "G11",
    goals: ["SAT_1500_PLUS"],
    languages: ["en"],
    history: {
      sat: [
        { math: 650, rw: 600, date: "2024-09-15" }
      ]
    }
  });
});

app.post("/api/profile", (req, res) => {
  res.json({
    message: "Profile updated successfully",
    profile: req.body
  });
});

// Error handling
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error("Error:", err);
  res.status(500).json({
    error: "Internal server error",
    message: err.message
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: "Not found",
    message: `Route ${req.method} ${req.path} not found`
  });
});

const PORT = process.env.PORT || 8000;

app.listen(PORT, () => {
  console.log(`DreamSeedAI API listening on :${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Diagnostics: http://localhost:${PORT}/api/diagnostics/run`);
});

export default app;


