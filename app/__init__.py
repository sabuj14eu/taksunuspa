# -*- coding: utf-8 -*-
"""Taksu Nusa Spa — application factory."""
from datetime import date

from flask import Flask, redirect, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import db, login_manager
from .i18n import lang, t, loc
from .money import rp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # nginx terminates TLS and proxies over plain HTTP, so without this Flask
    # thinks every request is http:// and same-site redirect checks fail.
    # A no-op when the X-Forwarded-* headers are absent, as in local dev.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from . import models  # noqa: F401  register every table

    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.public.routes import bp as public_bp
    from .blueprints.spa.routes import bp as spa_bp
    from .blueprints.shop.routes import bp as shop_bp
    from .blueprints.admin.routes import bp as admin_bp
    from .blueprints.seo.routes import bp as seo_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(spa_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(seo_bp)

    @app.before_request
    def _seo_middleware():
        """301 for changed slugs, plus a first-party pageview counter."""
        if request.method != "GET" or request.path.startswith(
                ("/static", "/admin", "/api")):
            return None
        try:
            from .models.shared import Redirect, PageView
            r = Redirect.query.filter_by(old_path=request.path).first()
            if r:
                return redirect(r.new_path, 301)
            pv = PageView.query.filter_by(path=request.path[:300],
                                          day=date.today()).first()
            if pv:
                pv.count += 1
            else:
                db.session.add(PageView(path=request.path[:300],
                                        day=date.today(), count=1))
            db.session.commit()
        except Exception:
            db.session.rollback()
        return None

    @app.context_processor
    def _inject():
        from .models.site import SiteSetting, Page, MenuItem
        from .models.shop import ProductGroup
        from .models.media import MediaImage
        from .models.spa import ServiceArea, TreatmentCategory
        from .services import media_service, pricing_service
        from .services.notify_service import whatsapp_link
        try:
            cfg = SiteSetting.all_dict()
            nav = (MenuItem.query.filter_by(is_visible=True)
                   .order_by(MenuItem.sort_order, MenuItem.id).all())
            footer_pages = (Page.query.filter_by(is_visible=True,
                                                 show_in_menu=True)
                            .order_by(Page.sort_order, Page.id).all())
            # Same rule as the treatment groups: an empty one is not
            # offered until it holds a product.
            product_groups = [g for g in
                              ProductGroup.query.filter_by(is_active=True)
                              .order_by(ProductGroup.sort_order,
                                        ProductGroup.id).all()
                              if any(pr.is_active for pr in g.products)]
            # A group with nothing in it renders a page saying "Nothing
            # found", which a guest reads as a broken site. Body Rituals and
            # Packages are listed again the moment a treatment is added to
            # them, so nothing has to be switched back on by hand.
            spa_cats = [c for c in
                        TreatmentCategory.query.filter_by(is_active=True)
                        .order_by(TreatmentCategory.sort_order,
                                  TreatmentCategory.id).all()
                        if any(t.is_active for t in c.treatments)]
            # The Gallery menu item disappears while there is nothing to
            # show, and returns on its own with the first photo.
            has_gallery = MediaImage.query.filter_by(
                entity_type="gallery").first() is not None
            areas_line = " · ".join(
                a.name for a in ServiceArea.query.filter_by(is_active=True)
                .order_by(ServiceArea.sort_order, ServiceArea.name).all())
            banner = next((d for d in pricing_service.live_discounts()
                           if d.is_automatic), None)
        except Exception:
            cfg, nav, footer_pages = {}, [], []
            product_groups, spa_cats, banner = [], [], None
            areas_line, has_gallery = "", False

        wa_number = cfg.get("whatsapp") or app.config["WHATSAPP_NUMBER"]
        return {
            "site": cfg, "nav_items": nav, "footer_pages": footer_pages,
            "product_groups": product_groups, "spa_cats": spa_cats,
            "areas_line": areas_line, "has_gallery": has_gallery,
            "how_it_works": _how_it_works_steps(),
            "banner_discount": banner,
            "t": t(), "lang": lang(), "loc": loc, "rp": rp,
            "cover_url": media_service.cover_url,
            "rating_of": media_service.rating_of,
            "price_of": pricing_service.price_of,
            "wa_number": wa_number,
            "wa": lambda text="": whatsapp_link(wa_number, text),
            "site_url": app.config["SITE_URL"],
            "cart_count": _cart_count(),
            "current_path": request.path,
            "year": date.today().year,
        }

    @app.template_filter("nl2br")
    def _nl2br(text):
        from markupsafe import Markup, escape
        return Markup("<br>".join(escape(text or "").split("\n")))

    @app.template_filter("richtext")
    def _richtext(text):
        """Page bodies, with headings. A line beginning "## " becomes a
        subheading and blank lines separate paragraphs, so a long page like
        About Us reads as sections instead of one wall of text. Everything is
        escaped first, so admin copy can never inject markup."""
        from markupsafe import Markup, escape
        out = []
        for block in (text or "").replace("\r\n", "\n").split("\n\n"):
            block = block.strip()
            if not block:
                continue
            if block.startswith("## "):
                head, _, rest = block.partition("\n")
                out.append(f"<h3>{escape(head[3:].strip())}</h3>")
                block = rest.strip()
                if not block:
                    continue
            body = "<br>".join(escape(line) for line in block.split("\n"))
            out.append(f"<p>{body}</p>")
        return Markup("".join(out))

    @app.errorhandler(404)
    def _404(_e):
        from flask import render_template
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def _too_large(_e):
        """Without this an oversized photo returns a bare browser error and
        the person is left guessing what went wrong."""
        from flask import flash, redirect
        limit = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        flash(f"That file is too big — the limit is {limit} MB. "
              f"Please resize the photo and try again.")
        return redirect(request.referrer or "/admin/media"), 302

    return app


def _how_it_works_steps():
    """The three steps, available to every page that shows the band."""
    from .blueprints.public.routes import HOW_IT_WORKS
    return HOW_IT_WORKS.get(lang(), HOW_IT_WORKS["en"])


def _cart_count():
    try:
        cart = session.get("cart")
        return sum(int(v) for v in cart.values()) if isinstance(cart, dict) else 0
    except Exception:
        return 0
