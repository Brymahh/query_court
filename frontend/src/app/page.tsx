"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  ReviewEvent,
  streamReview,
} from "@/lib/review-stream";

const eventLabels: Record<string, string> = {
  request_received: "Case Submission",
  draft_created: "Generator:",
  critique_created: "Critic Review:",
  verdict_issued: "Court Verdict",
};

export default function Home() {
  const [dialect, setDialect] = useState("postgres");
  const [request, setRequest] = useState("");
  const [schemaNotes, setSchemaNotes] = useState("");
  const [events, setEvents] = useState<ReviewEvent[]>([]);
  const [error, setError] = useState("");
  const [isReviewing, setIsReviewing] = useState(false);

  const latestDraft = useMemo(
    () =>
      [...events]
        .reverse()
        .find((event) => event.event_type === "draft_created"),
    [events],
  );

  const latestVerdict = useMemo(
    () =>
      [...events]
        .reverse()
        .find((event) => event.event_type === "verdict_issued"),
    [events],
  );

  async function handleSubmit(
    submitEvent: FormEvent<HTMLFormElement>,
  ) {
    submitEvent.preventDefault();

    setEvents([]);
    setError("");
    setIsReviewing(true);

    const fullRequest = schemaNotes.trim()
      ? `${request}\n\nSchema notes:\n${schemaNotes}`
      : request;

    await streamReview(
      {
        natural_language_request: fullRequest,
        dialect,
        maximum_rounds: 3,
      },
      (incomingEvent) => {
        setEvents((currentEvents) => [
          ...currentEvents,
          incomingEvent,
        ]);
      },
      (message) => {
        setError(message);
      },
    );

    setIsReviewing(false);
  }

  const verdictChecks =
    latestVerdict?.data.checks ??
    events.find((event) => event.data.checks)?.data.checks ??
    [];

  return (
    <main className="app-shell">
      <nav className="topbar">
        <div className="brand">
          <span className="brand-mark">Q</span>
          <span>QUERY-COURT</span>
        </div>

        <div className={`status-pill ${isReviewing ? "live" : ""}`}>
          {isReviewing ? "Review in progress" : "Ready for review"}
        </div>
      </nav>

      <section className="hero">
        <p className="eyebrow">SQL generation, under examination&gt;&gt;&gt;&gt;&gt;&gt;</p>

        <h1>
          Make your query
          <br />
          <span>defend itself.</span>
        </h1>

        <p className="hero-copy">
          Ask for SQL in plain language. Watch the generator draft,
          the critic challenge, and the court issue a verdict.
        </p>
      </section>

      <section className="workspace">
        <section className="panel">
          <div className="panel-header">
            <h2>Bring a case</h2>
          </div>

          <div className="panel-body">
            <form className="form-stack" onSubmit={handleSubmit}>
              <div className="field">
                <label htmlFor="dialect">SQL dialect</label>

                <select
                  id="dialect"
                  value={dialect}
                  onChange={(event) => setDialect(event.target.value)}
                >
                  <option value="postgres">PostgreSQL</option>
                  <option value="mysql">MySQL</option>
                  <option value="sqlite">SQLite</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="request">
                  Plain-language request
                </label>

                <textarea
                  id="request"
                  value={request}
                  onChange={(event) => setRequest(event.target.value)}
                  placeholder="Find the five highest-value customers."
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="schema">
                  Schema notes (Optional)
                </label>

                <textarea
                  id="schema"
                  value={schemaNotes}
                  onChange={(event) =>
                    setSchemaNotes(event.target.value)
                  }
                  placeholder="customers(id, name, lifetime_value)"
                />
              </div>

              <button
                className="primary-button"
                type="submit"
                disabled={isReviewing}
              >
                {isReviewing ? "Examining..." : "Bring to court"}
              </button>
            </form>

            {error && (
              <div className="error-box" role="alert">
                {error}
              </div>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Proceedings</h2>
            <span>{events.length} events</span>
          </div>

          <div className="panel-body">
            {events.length === 0 ? (
              <div className="empty-state">
                <p>
                  The court is waiting.
                  <br />
                  Submit a request to begin.
                </p>
              </div>
            ) : (
              <div className="timeline" aria-live="polite">
                {events.map((event, index) => (
                  <article
                    className={`event ${event.event_type}`}
                    key={`${event.event_type}-${index}`}
                  >
                    <p className="event-label">
                      {eventLabels[event.event_type] ??
                        event.event_type}
                    </p>

                    <p className="event-message">
                      {event.message}
                    </p>

                    {event.data.sql && (
                      <pre className="sql-block">
                        {event.data.sql}
                      </pre>
                    )}

                    {event.data.summary && (
                      <p className="event-message">
                        {event.data.summary}
                      </p>
                    )}

                    {event.data.checks && (
                      <div className="check-list">
                        {event.data.checks.map((check) => (
                          <div className="check" key={check.name}>
                            <span>
                              <strong>{check.name}</strong>
                              <br />
                              {check.evidence}
                            </span>

                            <span
                              className={`check-status ${check.status}`}
                            >
                              {check.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            )}

            {latestDraft?.data.sql && latestVerdict && (
              <section className="verdict">
                <div className="verdict-title">
                  <div className="verdict-heading">
                    <span className="verdict-eyebrow">FINAL DELIVERABLE</span>

                    <h3>Adjudicated Query</h3>

                    <p className="verdict-subtitle">
                      The approved SQL statement, ready for execution.
                    </p>
                  </div>
                  <span className="verdict-status">
                    {latestVerdict.data.status ?? "reviewed"}
                  </span>
                </div>

                <pre className="sql-block">
                  {latestVerdict.data.final_sql ??
                    latestDraft.data.sql}
                </pre>

                {verdictChecks.length > 0 && (
                  <div className="check-list">
                    {verdictChecks.map((check) => (
                      <div className="check" key={check.name}>
                        <span>{check.evidence}</span>
                        <span
                          className={`check-status ${check.status}`}
                        >
                          {check.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}
// "use client";

// import { FormEvent, useState } from "react";
// import { streamReview, ReviewEvent } from "@/lib/review-stream";

// export default function Home() {
//   const [dialect, setDialect] = useState("postgres");
//   const [request, setRequest] = useState("");
//   const [ddl, setDdl] = useState("");
//   const [events, setEvents] = useState<ReviewEvent[]>([]);
//   const [error, setError] = useState("");
//   const [isLoading, setIsLoading] = useState(false);

//   async function handleSubmit(event: FormEvent<HTMLFormElement>) {
//     event.preventDefault();

//     setEvents([]);
//     setError("");
//     setIsLoading(true);

//     await streamReview(
//       {
//         natural_language_request: ddl
//           ? `${request}\n\nSchema context:\n${ddl}`
//           : request,
//         dialect,
//         maximum_rounds: 3,
//       },
//       (reviewEvent) => {
//         setEvents((current) => [...current, reviewEvent]);
//       },
//       (message) => {
//         setError(message);
//       },
//     );

//     setIsLoading(false);
//   }

//   return (
//     <main>
//       <header>
//         <p>QUERY-COURT</p>
//         <h1>Make SQL defend itself.</h1>
//         <p>
//           A generator drafts. A critic cross-examines. The evidence stays
//           visible.
//         </p>
//       </header>

//       <form onSubmit={handleSubmit}>
//         <label>
//           SQL dialect
//           <select
//             value={dialect}
//             onChange={(event) => setDialect(event.target.value)}
//           >
//             <option value="postgres">PostgreSQL</option>
//             <option value="mysql">MySQL</option>
//             <option value="sqlite">SQLite</option>
//           </select>
//         </label>

//         <label>
//           Request
//           <textarea
//             value={request}
//             onChange={(event) => setRequest(event.target.value)}
//             placeholder="Find the five highest-value customers."
//             required
//           />
//         </label>

//         <label>
//           Optional schema context
//           <textarea
//             value={ddl}
//             onChange={(event) => setDdl(event.target.value)}
//             placeholder="Paste DDL or table details when available."
//           />
//         </label>

//         <button type="submit" disabled={isLoading}>
//           {isLoading ? "Reviewing..." : "Bring to court"}
//         </button>
//       </form>

//       {error && <p role="alert">{error}</p>}

//       <section aria-live="polite">
//         {events.map((reviewEvent, index) => (
//           <article key={`${reviewEvent.event_type}-${index}`}>
//             <small>{reviewEvent.event_type}</small>
//             <p>{reviewEvent.message}</p>

//             {reviewEvent.data.sql && (
//               <pre>{String(reviewEvent.data.sql)}</pre>
//             )}

//             {reviewEvent.data.summary && (
//               <p>{String(reviewEvent.data.summary)}</p>
//             )}
//           </article>
//         ))}
//       </section>
//     </main>
//   );
// }
