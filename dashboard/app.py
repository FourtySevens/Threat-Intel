"""Flask application factory for the read-only search dashboard."""

from __future__ import annotations

import logging
from math import ceil

from flask import Flask, abort, g, render_template, request

from dashboard.db import get_readonly_conn
from dashboard.repository import PAGE_SIZE, SearchFilters, get_article, get_cve, get_filter_values, get_metrics, search_articles, search_cves

LOGGER = logging.getLogger(__name__)


def _page(value: str | None) -> int:
    try:
        return max(1, int(value or "1"))
    except ValueError:
        return 1


def _conn():
    if "db" not in g:
        g.db = get_readonly_conn()
    return g.db


def create_app() -> Flask:
    app = Flask(__name__)

    @app.teardown_appcontext
    def close_connection(_error=None):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    @app.get("/")
    def index():
        filters = SearchFilters(
            query=request.args.get("q", "").strip()[:200],
            severity=request.args.get("severity", "").strip()[:20],
            source=request.args.get("source", "").strip()[:50],
            kev=request.args.get("kev", "").strip(),
            page=_page(request.args.get("page")),
        )
        conn = _conn()
        results, total = search_cves(conn, filters)
        return render_template(
            "index.html",
            metrics=get_metrics(conn),
            filter_values=get_filter_values(conn),
            filters=filters,
            results=results,
            articles=search_articles(conn, filters.query),
            total=total,
            page_count=max(1, ceil(total / PAGE_SIZE)),
        )

    @app.get("/cves/<cve_id>")
    def cve_detail(cve_id: str):
        cve = get_cve(_conn(), cve_id.upper())
        if cve is None:
            abort(404)
        return render_template("cve_detail.html", cve=cve)

    @app.get("/articles/<int:article_id>")
    def article_detail(article_id: int):
        article = get_article(_conn(), article_id)
        if article is None:
            abort(404)
        return render_template("article_detail.html", article=article)

    @app.get("/healthz")
    def healthz():
        with _conn().cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ok"}

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", status=404, message="That record was not found."), 404

    @app.errorhandler(Exception)
    def internal_error(error):
        LOGGER.exception("dashboard request failed")
        return render_template("error.html", status=500, message="The dashboard could not complete this request."), 500

    return app


if __name__ == "__main__":
    from config.settings import get_settings

    settings = get_settings()
    create_app().run(host=settings.dashboard_host, port=settings.dashboard_port, debug=False)
