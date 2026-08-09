"use client";

import { useState } from "react";
import { LESSONS, SECTIONS, type Lesson } from "@/lib/lessons";

type Lang = "en" | "hi";

export default function Education() {
  const [lang, setLang] = useState<Lang>("en");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function sectionLessons(sectionId: string): Lesson[] {
    return LESSONS.filter((l) => l.section === sectionId);
  }

  return (
    <section className="card">
      <div className="row">
        <h2>{lang === "en" ? "Learning Center" : "Learning Center"}</h2>
        <div className="lang-toggle">
          <button
            className={lang === "en" ? "active" : "ghost"}
            onClick={() => setLang("en")}
          >
            EN
          </button>
          <button
            className={lang === "hi" ? "active" : "ghost"}
            onClick={() => setLang("hi")}
          >
            HI
          </button>
        </div>
      </div>

      {SECTIONS.map((section) => {
        const lessons = sectionLessons(section.id);
        return (
          <div key={section.id} className="lesson-section">
            <h3>{section.title[lang]}</h3>
            {lessons.map((lesson) => (
              <div key={lesson.id} className="lesson-card">
                <button
                  className="lesson-header"
                  onClick={() => toggle(lesson.id)}
                >
                  <span className="lesson-arrow">{expanded.has(lesson.id) ? "▾" : "▸"}</span>
                  <strong>{lesson.title[lang]}</strong>
                </button>
                {expanded.has(lesson.id) && (
                  <div className="lesson-body">
                    {lesson.body[lang].split("\n\n").map((para, i) => (
                      <p key={i} className="lesson-para">{para}</p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      })}
    </section>
  );
}
