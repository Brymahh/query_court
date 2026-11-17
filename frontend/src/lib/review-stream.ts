export type CheckResult = {
  name: string;
  status: "passed" | "failed" | "unavailable" | "warning";
  evidence: string;
};

export type ReviewEvent = {
  event_type: string;
  message: string;
  round_number?: number;
  data: {
    sql?: string;
    dialect?: string;
    summary?: string;
    requested_revision?: string | null;
    status?: string;
    rationale?: string;
    checks?: CheckResult[];
    final_sql?: string | null;
  };
};

type ReviewRequest = {
  natural_language_request: string;
  dialect: string;
  maximum_rounds: number;
};

export async function streamReview(
  request: ReviewRequest,
  onEvent: (event: ReviewEvent) => void,
  onError: (message: string) => void,
): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  if (!apiUrl) {
    onError("NEXT_PUBLIC_API_URL is not configured.");
    return;
  }

  try {
    const response = await fetch(`${apiUrl}/reviews/stream`, {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      onError(await response.text());
      return;
    }

    if (!response.body) {
      onError("The backend returned no stream.");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        const dataLine = frame
          .split("\n")
          .find((line) => line.startsWith("data:"));

        if (!dataLine) {
          continue;
        }

        try {
          const payload = dataLine.slice(5).trim();
          onEvent(JSON.parse(payload) as ReviewEvent);
        } catch {
          onError("The backend sent invalid event data.");
        }
      }
    }
  } catch {
    onError("Could not connect to the Query-Court backend.");
  }
}
// export type ReviewEvent = {
//   event_type: string;
//   message: string;
//   round_number?: number;
//   data: Record<string, unknown>;
// };

// type ReviewRequest = {
//   natural_language_request: string;
//   dialect: string;
//   maximum_rounds: number;
// };

// export async function streamReview(
//   request: ReviewRequest,
//   onEvent: (event: ReviewEvent) => void,
//   onError: (message: string) => void,
// ): Promise<void> {
//   const apiUrl = process.env.NEXT_PUBLIC_API_URL;

//   if (!apiUrl) {
//     onError("Backend API URL is not configured.");
//     return;
//   }

//   const response = await fetch(`${apiUrl}/reviews/stream`, {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//       Accept: "text/event-stream",
//     },
//     body: JSON.stringify(request),
//   });

//   if (!response.ok) {
//     const errorBody = await response.text();
//     onError(errorBody || `Request failed with status ${response.status}.`);
//     return;
//   }

//   if (!response.body) {
//     onError("Backend returned no streaming response.");
//     return;
//   }

//   const reader = response.body.getReader();
//   const decoder = new TextDecoder();
//   let buffer = "";

//   while (true) {
//     const { value, done } = await reader.read();

//     if (done) {
//       break;
//     }

//     buffer += decoder.decode(value, { stream: true });

//     const frames = buffer.split("\n\n");
//     buffer = frames.pop() ?? "";

//     for (const frame of frames) {
//       const dataLine = frame
//         .split("\n")
//         .find((line) => line.startsWith("data:"));

//       if (!dataLine) {
//         continue;
//       }

//       const json = dataLine.slice("data:".length).trim();

//       try {
//         onEvent(JSON.parse(json) as ReviewEvent);
//       } catch {
//         onError("Backend sent invalid event data.");
//       }
//     }
//   }
// }
