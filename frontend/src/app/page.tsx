"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  Check,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  Copy,
  LoaderCircle,
  Scale,
  TriangleAlert,
  X,
} from "lucide-react";
import { ReviewEvent, streamReview } from "@/lib/review-stream";

const eventLabels: Record<string, string> = {
  request_received: "Case submission",
  draft_created: "Generator draft",
  critique_created: "Critic evidence",
  verdict_issued: "Court verdict",
};

const statusIcons = {
  passed: CheckCircle2,
  failed: X,
  unavailable: CircleHelp,
  warning: TriangleAlert,
};

export default function Home() {
  const [dialect, setDialect] = useState("postgres");
  const [request, setRequest] = useState("");
  const [schemaNotes, setSchemaNotes] = useState("");
  const [events, setEvents] = useState<ReviewEvent[]>([]);
  const [error, setError] = useState("");
  const [isReviewing, setIsReviewing] = useState(false);
  const [copiedSql, setCopiedSql] = useState(false);

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

  const latestChecks = useMemo(
    () => {
      const critique = [...events]
        .reverse()
        .find((event) => event.event_type === "critique_created");

      return critique?.data.checks ?? [];
    },
    [events],
  );

  async function handleSubmit(
    submitEvent: FormEvent<HTMLFormElement>,
  ) {
    submitEvent.preventDefault();

    setEvents([]);
    setError("");
    setCopiedSql(false);
    setIsReviewing(true);

    const fullRequest = schemaNotes.trim()
      ? `${request.trim()}\n\nSchema notes:\n${schemaNotes.trim()}`
      : request.trim();

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
      (message) => setError(message),
    );

    setIsReviewing(false);
  }

  async function copySql(sql: string) {
    await navigator.clipboard.writeText(sql);
    setCopiedSql(true);
    window.setTimeout(() => setCopiedSql(false), 1800);
  }

  return (
    <main className="app-shell">
      <nav className="topbar">
        <div className="brand">
          <span className="brand-mark">
            <Scale aria-hidden="true" size={16} />
          </span>
          <span>QUERY-COURT</span>
        </div>

        <div className={`status-pill ${isReviewing ? "live" : ""}`}>
          <span className={isReviewing ? "status-dot pulse" : "status-dot"} />
          {isReviewing ? "Court in session" : "Ready"}
        </div>
      </nav>

      <header className="hero">
        <p className="eyebrow">SQL generation under examination&gt;&gt;&gt;&gt;&gt;&gt;</p>
        <h1>
          Make your query
          <br />
          <span>defend itself.</span>
        </h1>
        <p className="hero-copy">
          Submit a request. Watch the generator draft and the critic
          examine the evidence before the court rules.
        </p>
      </header>

      <section className="workspace">
        <aside className="panel case-panel">
          <div className="panel-header">
            <h2>Bring a case</h2>
            {/* <span className="step-count">01</span> */}
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
                <label htmlFor="request">Plain-language request</label>
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
                  Schema notes <span>Optional</span>
                </label>
                <textarea
                  id="schema"
                  value={schemaNotes}
                  onChange={(event) => setSchemaNotes(event.target.value)}
                  placeholder=
                  {["Paste your schema notes here e.g.",
                  "CREATE TABLE books (",
                    "  book_id INTEGER NOT NULL,",
                    "  title VARCHAR(255) NOT NULL,",
                    "  author VARCHAR(255),",
                    "  category VARCHAR(100),",
                    "  published_year INTEGER);"
                    ].join("\n")}
                    // style={{ fontSize: "12px" }}
                  // "customers(id, name, lifetime_value)"
                />
              </div>

              <button
                className="primary-button"
                type="submit"
                disabled={isReviewing}
              >
                {isReviewing ? (
                  <>
                    <LoaderCircle className="button-spinner" size={17} />
                    Examining
                  </>
                ) : (
                  "Bring to court"
                )}
              </button>
            </form>

            {error && (
              <div className="error-box" role="alert">
                <TriangleAlert size={16} />
                <span>{error}</span>
              </div>
            )}
          </div>
        </aside>

        <section className="panel proceedings-panel">
          <div className="panel-header">
            <h2>Proceedings</h2>
            <span className="event-count">
              {events.length} {events.length === 1 ? "event" : "events"}
            </span>
          </div>

          <div className="panel-body proceedings-body">
            {events.length === 0 && !isReviewing ? (
              <div className="empty-state">
                <Scale size={28} aria-hidden="true" />
                <p>The court is waiting.</p>
                <small>Submit a request to begin proceedings.</small>
              </div>
            ) : (
              <div className="timeline" aria-live="polite">
                {events.map((event, index) => (
                  <TimelineEvent
                    key={`${event.event_type}-${index}`}
                    event={event}
                    latestDraft={latestDraft}
                    latestVerdict={latestVerdict}
                    copiedSql={copiedSql}
                    onCopy={copySql}
                    isFinal={event.event_type === "verdict_issued"}
                  />
                ))}

                {isReviewing &&
                  latestVerdict === undefined &&
                  <div className="pending-event">
                    <div className="pending-marker">
                      <LoaderCircle size={18} />
                    </div>
                    <div className="pending-card">
                      <span>Evidence review</span>
                      <p>The court is examining the latest evidence.</p>
                    </div>
                  </div>
                }
              </div>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

type TimelineEventProps = {
  event: ReviewEvent;
  latestDraft: ReviewEvent | undefined;
  latestVerdict: ReviewEvent | undefined;
  copiedSql: boolean;
  onCopy: (sql: string) => Promise<void>;
  isFinal: boolean;
};

function TimelineEvent({
  event,
  latestDraft,
  latestVerdict,
  copiedSql,
  onCopy,
  isFinal,
}: TimelineEventProps) {
  const sql =
    event.event_type === "draft_created"
      ? event.data.sql
      : event.event_type === "verdict_issued"
        ? event.data.final_sql ?? latestDraft?.data.sql
        : undefined;

  const checks = event.data.checks ?? [];

  return (
    <article className={`timeline-event event-${event.event_type}`}>
      <div className="timeline-marker" aria-hidden="true">
        {event.event_type === "request_received" && "1"}
        {event.event_type === "draft_created" && "2"}
        {event.event_type === "critique_created" && "3"}
        {event.event_type === "verdict_issued" && "4"}
      </div>

      <div className="event-card">
        <div className="event-heading">
          <span className={`event-badge badge-${event.event_type}`}>
            {eventLabels[event.event_type] ?? event.event_type}
          </span>

          {event.round_number && (
            <span className="round-label">Round {event.round_number}</span>
          )}
        </div>

        <p className="event-message">{event.message}</p>

        {sql && (
          <details className="sql-details" open={isFinal}>
            <summary>
              <span>{isFinal ? "Adjudicated SQL" : "Generated SQL"}</span>
              <span className="details-action">
                <span>Expand</span>
                <ChevronDown size={15} />
              </span>
            </summary>

            <div className="sql-scroll">
              <pre>{sql}</pre>
            </div>

            <button
              className="copy-button"
              type="button"
              onClick={() => void onCopy(sql)}
            >
              {copiedSql ? (
                <>
                  <Check size={14} /> Copied
                </>
              ) : (
                <>
                  <Copy size={14} /> Copy SQL
                </>
              )}
            </button>
          </details>
        )}

        {event.event_type === "critique_created" && (
          <>
            {/* {event.data.summary && (
              <div className="critic-summary">
                <span>Critic summary</span>
                <p>{event.data.summary}</p>
              </div>
            )} */}
            {event.data.requested_revision && (
              <div className="revision-note">
                <TriangleAlert size={16} />
                <span>
                  <strong>Revision requested</strong>
                  {event.data.requested_revision}
                </span>
              </div>
            )}

            {checks.length > 0 && (
              <div className="check-grid">
                {checks.map((check) => {
                  const Icon =
                    statusIcons[
                      check.status as keyof typeof statusIcons
                    ];

                  return (
                    <div className="check-row" key={check.name}>
                      <div className={`check-icon ${check.status}`}>
                        <Icon size={15} />
                      </div>
                      <div>
                        <strong>{check.name}</strong>
                        <p>{check.evidence}</p>
                      </div>
                      <span className={`check-status ${check.status}`}>
                        {check.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {isFinal && latestVerdict?.data.status && (
          <div className={`verdict-strip ${latestVerdict.data.status}`}>
            <span>Verdict</span>
            <strong>{latestVerdict.data.status.replace("_", " ")}</strong>
          </div>
        )}
      </div>
    </article>
  );
}

// "use client";

// import { FormEvent, useMemo, useState } from "react";
// import {
//   ReviewEvent,
//   streamReview,
// } from "@/lib/review-stream";

// const eventLabels: Record<string, string> = {
//   request_received: "Case Submission",
//   draft_created: "Generator:",
//   critique_created: "Critic Review:",
//   verdict_issued: "Court Verdict",
// };

// export default function Home() {
//   const [dialect, setDialect] = useState("postgres");
//   const [request, setRequest] = useState("");
//   const [schemaNotes, setSchemaNotes] = useState("");
//   const [events, setEvents] = useState<ReviewEvent[]>([]);
//   const [error, setError] = useState("");
//   const [isReviewing, setIsReviewing] = useState(false);

//   const latestDraft = useMemo(
//     () =>
//       [...events]
//         .reverse()
//         .find((event) => event.event_type === "draft_created"),
//     [events],
//   );

//   const latestVerdict = useMemo(
//     () =>
//       [...events]
//         .reverse()
//         .find((event) => event.event_type === "verdict_issued"),
//     [events],
//   );

//   async function handleSubmit(
//     submitEvent: FormEvent<HTMLFormElement>,
//   ) {
//     submitEvent.preventDefault();

//     setEvents([]);
//     setError("");
//     setIsReviewing(true);

//     const fullRequest = schemaNotes.trim()
//       ? `${request}\n\nSchema notes:\n${schemaNotes}`
//       : request;

//     await streamReview(
//       {
//         natural_language_request: fullRequest,
//         dialect,
//         maximum_rounds: 3,
//       },
//       (incomingEvent) => {
//         setEvents((currentEvents) => [
//           ...currentEvents,
//           incomingEvent,
//         ]);
//       },
//       (message) => {
//         setError(message);
//       },
//     );

//     setIsReviewing(false);
//   }

//   const verdictChecks =
//     latestVerdict?.data.checks ??
//     events.find((event) => event.data.checks)?.data.checks ??
//     [];

//   return (
//     <main className="app-shell">
//       <nav className="topbar">
//         <div className="brand">
//           <span className="brand-mark">Q</span>
//           <span>QUERY-COURT</span>
//         </div>

//         <div className={`status-pill ${isReviewing ? "live" : ""}`}>
//           {isReviewing ? "Review in progress" : "Ready for review"}
//         </div>
//       </nav>

//       <section className="hero">
//         <p className="eyebrow">SQL generation, under examination&gt;&gt;&gt;&gt;&gt;&gt;</p>

//         <h1>
//           Make your query
//           <br />
//           <span>defend itself.</span>
//         </h1>

//         <p className="hero-copy">
//           Ask for SQL in plain language. Watch the generator draft,
//           the critic challenge, and the court issue a verdict.
//         </p>
//       </section>

//       <section className="workspace">
//         <section className="panel">
//           <div className="panel-header">
//             <h2>Bring a case</h2>
//           </div>

//           <div className="panel-body">
//             <form className="form-stack" onSubmit={handleSubmit}>
//               <div className="field">
//                 <label htmlFor="dialect">SQL dialect</label>

//                 <select
//                   id="dialect"
//                   value={dialect}
//                   onChange={(event) => setDialect(event.target.value)}
//                 >
//                   <option value="postgres">PostgreSQL</option>
//                   <option value="mysql">MySQL</option>
//                   <option value="sqlite">SQLite</option>
//                 </select>
//               </div>

//               <div className="field">
//                 <label htmlFor="request">
//                   Plain-language request
//                 </label>

//                 <textarea
//                   id="request"
//                   value={request}
//                   onChange={(event) => setRequest(event.target.value)}
//                   placeholder="Find the five highest-value customers."
//                   required
//                 />
//               </div>

//               <div className="field">
//                 <label htmlFor="schema">
//                   Schema notes (Optional)
//                 </label>

//                 <textarea
//                   id="schema"
//                   value={schemaNotes}
//                   onChange={(event) =>
//                     setSchemaNotes(event.target.value)
//                   }
//                   placeholder="customers(id, name, lifetime_value)"
//                 />
//               </div>

//               <button
//                 className="primary-button"
//                 type="submit"
//                 disabled={isReviewing}
//               >
//                 {isReviewing ? "Examining..." : "Bring to court"}
//               </button>
//             </form>

//             {error && (
//               <div className="error-box" role="alert">
//                 {error}
//               </div>
//             )}
//           </div>
//         </section>

//         <section className="panel">
//           <div className="panel-header">
//             <h2>Proceedings</h2>
//             <span>{events.length} events</span>
//           </div>

//           <div className="panel-body">
//             {events.length === 0 ? (
//               <div className="empty-state">
//                 <p>
//                   The court is waiting.
//                   <br />
//                   Submit a request to begin.
//                 </p>
//               </div>
//             ) : (
//               <div className="timeline" aria-live="polite">
//                 {events.map((event, index) => (
//                   <article
//                     className={`event ${event.event_type}`}
//                     key={`${event.event_type}-${index}`}
//                   >
//                     <p className="event-label">
//                       {eventLabels[event.event_type] ??
//                         event.event_type}
//                     </p>

//                     <p className="event-message">
//                       {event.message}
//                     </p>

//                     {event.data.sql && (
//                       <pre className="sql-block">
//                         {event.data.sql}
//                       </pre>
//                     )}

//                     {event.data.summary && (
//                       <p className="event-message">
//                         {event.data.summary}
//                       </p>
//                     )}

//                     {event.data.checks && (
//                       <div className="check-list">
//                         {event.data.checks.map((check) => (
//                           <div className="check" key={check.name}>
//                             <span>
//                               <strong>{check.name}</strong>
//                               <br />
//                               {check.evidence}
//                             </span>

//                             <span
//                               className={`check-status ${check.status}`}
//                             >
//                               {check.status}
//                             </span>
//                           </div>
//                         ))}
//                       </div>
//                     )}
//                   </article>
//                 ))}
//               </div>
//             )}

//             {latestDraft?.data.sql && latestVerdict && (
//               <section className="verdict">
//                 <div className="verdict-title">
//                   <div className="verdict-heading">
//                     <span className="verdict-eyebrow">FINAL DELIVERABLE</span>

//                     <h3>Adjudicated Query</h3>

//                     <p className="verdict-subtitle">
//                       The approved SQL statement, ready for execution.
//                     </p>
//                   </div>
//                   <span className="verdict-status">
//                     {latestVerdict.data.status ?? "reviewed"}
//                   </span>
//                 </div>

//                 <pre className="sql-block">
//                   {latestVerdict.data.final_sql ??
//                     latestDraft.data.sql}
//                 </pre>

//                 {verdictChecks.length > 0 && (
//                   <div className="check-list">
//                     {verdictChecks.map((check) => (
//                       <div className="check" key={check.name}>
//                         <span>{check.evidence}</span>
//                         <span
//                           className={`check-status ${check.status}`}
//                         >
//                           {check.status}
//                         </span>
//                       </div>
//                     ))}
//                   </div>
//                 )}
//               </section>
//             )}
//           </div>
//         </section>
//       </section>
//     </main>
//   );
// }
