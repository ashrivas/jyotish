from datetime import date as CivilDate, datetime, time as CivilTime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Conventions(StrictModel):
    version: Literal["conventions.v1-draft"] = "conventions.v1-draft"
    zodiac: Literal["sidereal"] = "sidereal"
    ayanamsa: Literal["lahiri"] = "lahiri"
    nodes: Literal["mean", "true"] = "mean"
    houses: Literal["whole_sign"] = "whole_sign"
    dasha_year_days: Literal[365.25, 365.2425, 360.0] = 365.25
    varga_method: Literal["pvr-2000-ch6"] = "pvr-2000-ch6"
    sunrise: Literal["upper_limb_standard_refraction"] = "upper_limb_standard_refraction"


class BirthInput(StrictModel):
    date: CivilDate
    time: CivilTime | None = None
    latitude: float = Field(ge=-89.0, le=89.0)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = Field(min_length=1, max_length=80)
    place: str = Field(default="Manual coordinates", max_length=120)
    confidence: Literal["exact", "certificate", "family", "custom", "unknown"] = "certificate"
    uncertainty_minutes: float | None = Field(default=None, ge=0, le=720)
    fold: Literal[0, 1] | None = None
    civil_offset_seconds: int | None = Field(default=None, ge=-64800, le=64800)
    civil_offset_source: str | None = Field(default=None, min_length=3, max_length=300)

    @model_validator(mode="after")
    def check(self):
        if not 1900 <= self.date.year <= 2099:
            raise ValueError("This release supports Gregorian civil dates from 1900 through 2099.")
        if self.confidence != "unknown" and self.time is None:
            raise ValueError("Supply a birth time or choose unknown time.")
        if self.time and self.time.tzinfo:
            raise ValueError("Supply a local civil time without a UTC offset; the IANA zone resolves it.")
        if self.confidence == "custom" and self.uncertainty_minutes is None:
            raise ValueError("Custom confidence requires uncertainty_minutes.")
        if self.confidence != "custom" and self.uncertainty_minutes is not None:
            raise ValueError("uncertainty_minutes applies only to custom confidence.")
        if self.confidence == "unknown" and self.fold is not None:
            raise ValueError("A DST fold applies only to a known birth time.")
        if (self.civil_offset_seconds is None) != (self.civil_offset_source is None):
            raise ValueError(
                "A historical civil-time override requires both offset seconds and a record source."
            )
        if self.civil_offset_seconds is not None and self.fold is not None:
            raise ValueError("A recorded UTC offset already disambiguates the time; omit fold.")
        return self


class ChartRequest(StrictModel):
    birth: BirthInput
    conventions: Conventions = Field(default_factory=Conventions)
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    include_robustness: bool = True

    @model_validator(mode="after")
    def check(self):
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must include a UTC offset.")
        if not 1900 <= self.as_of.year <= 2099:
            raise ValueError("as_of must be in 1900..2099.")
        return self
