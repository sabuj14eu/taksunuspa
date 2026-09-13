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
        from .models.spa import TreatmentCategory
        from .services import media_service, pricing_service
        from .services.notify_service import whatsapp_link
        try:
            cfg = SiteSetting.all_dict()
            nav = (MenuItem.query.filter_by(is_visible=True)
                   .order_by(MenuItem.sort_order, MenuItem.id).all())
            footer_pages = (Page.query.filter_by(is_visible=True,
                                                 show_in_menu=True)
                            .order_by(Page.sort_order, Page.id).all())
            product_groups = (ProductGroup.query.filter_by(is_active=True)
                              .order_by(ProductGroup.sort_order,
                                        ProductGroup.id).all())
            spa_cats = (TreatmentCategory.query.filter_by(is_active=True)
                        .order_by(TreatmentCategory.sort_order,
                                  TreatmentCategory.id).all())
            banner = next((d for d in pricing_service.live_discounts()
                           if d.is_automatic), None)
        except Exception:
            cfg, nav, footer_pages = {}, [], []
            product_groups, spa_cats, banner = [], [], None

        wa_number = cfg.get("whatsapp") or app.config["WHATSAPP_NUMBER"]
        return {
            "site": cfg, "nav_items": nav, "footer_pages": footer_pages,
            "product_groups": product_groups, "spa_cats": spa_cats,
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

    @app.errorhandler(404)
    def _404(_e):
        from flask import render_template
        return render_template("404.html"), 404

    return app


def _cart_count():
    try:
        cart = session.get("cart")
        return sum(int(v) for v in cart.values()) if isinstance(cart, dict) else 0
    except Exception:
        return 0
