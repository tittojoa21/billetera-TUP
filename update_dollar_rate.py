from models import db, DollarRate
from datetime import datetime, date
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
import logging

def update_dollar_rate(
    buy_rate: float,
    sell_rate: float,
    blue_buy_rate: Optional[float] = None,
    blue_sell_rate: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> str:
    """
    Actualiza la tasa de cambio oficial y blue del dólar en la base de datos. Agrega una nueva entrada solo si la
    tasa de hoy no existe, para evitar duplicados.

    Args:
        buy_rate (float): Tasa de compra del dólar oficial.
        sell_rate (float): Tasa de venta del dólar oficial.
        blue_buy_rate (Optional[float]): Tasa de compra del dólar blue.
        blue_sell_rate (Optional[float]): Tasa de venta del dólar blue.
        logger (Optional[logging.Logger]): Objeto logger para registrar mensajes.

    Returns:
        str: Mensaje de éxito o error para la actualización de la tasa.
    """
    logger = logger or logging.getLogger(__name__)
    success_message = "Cotización actualizada con éxito."
    error_message = "Error al actualizar la cotización."

    if any(rate is not None and rate <= 0 for rate in [buy_rate, sell_rate, blue_buy_rate, blue_sell_rate]):
        error_msg = "Todas las tasas deben ser mayores que cero."
        logger.error(error_msg)
        return error_msg

    try:
        today = date.today()
        existing_rate = DollarRate.query.filter(func.date(DollarRate.timestamp) == today).first()

        if existing_rate:
            existing_rate.buy_rate = round(buy_rate, 4)
            existing_rate.sell_rate = round(sell_rate, 4)
            if blue_buy_rate is not None:
                existing_rate.blue_buy_rate = round(blue_buy_rate, 4)
            if blue_sell_rate is not None:
                existing_rate.blue_sell_rate = round(blue_sell_rate, 4)
            existing_rate.timestamp = datetime.utcnow()
            logger.info(
                "Tasa existente actualizada para hoy: compra = %.4f, venta = %.4f, "
                "compra blue = %.4f, venta blue = %.4f",
                buy_rate, sell_rate, blue_buy_rate or 0, blue_sell_rate or 0
            )
        else:
            new_rate = DollarRate(
                buy_rate=round(buy_rate, 4),
                sell_rate=round(sell_rate, 4),
                blue_buy_rate=round(blue_buy_rate, 4) if blue_buy_rate else None,
                blue_sell_rate=round(blue_sell_rate, 4) if blue_sell_rate else None,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_rate)
            logger.info(
                "Nueva tasa agregada para hoy: compra = %.4f, venta = %.4f, "
                "compra blue = %.4f, venta blue = %.4f",
                buy_rate, sell_rate, blue_buy_rate or 0, blue_sell_rate or 0
            )
        

        db.session.commit()
        logger.info("Commit a la base de datos exitoso.")
        return success_message

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("%s: %s", error_message, str(e))
        return f"{error_message}: {str(e)}"
    except Exception as e:
        logger.error("Error inesperado: %s", str(e))
        return f"Error inesperado al actualizar la cotización: {str(e)}"

    finally:
        db.session.remove()
