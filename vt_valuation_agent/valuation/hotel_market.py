"""RNAADR: room-night analysis and ADR forecast (HVS built-up approach).

The built-up approach based on an analysis of lodging activity works as
follows:

1. Define the competitive set. Each competitor has a room count, the share of
   the base year it was open (giving the historic average room count, HARC),
   an occupancy, a demand segmentation and a competitive weight (1.0 for a
   primary competitor, less for a secondary one). Effective rooms are
   ``rooms x fraction_open x weight``.
2. Base-year accommodated demand per segment is the sum over competitors of
   ``HARC x 365 x occupancy x segment share``.
3. Each competitor's fair share is its effective rooms over the market's; its
   market share per segment is its accommodated room nights over the
   segment's; the penetration (competitive) index is market share / fair
   share. Indices above 1.0 mean the property captures more than its fair
   share of that segment.
4. Latent demand is added: unaccommodated demand (turned away by capacity
   constraints) and induced demand (created by a new generator). Each segment
   grows at its own rate.
5. In each projection year the subject and any new supply enter with their own
   room counts, opening fractions and penetration indices. Shares are the
   penetration-weighted effective rooms, normalised so the market's shares
   sum to one (the market share adjuster). Subject room nights, occupancy,
   segment ADRs and the blended ADR and RevPAR follow.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from pydantic import BaseModel, Field

DAYS = 365.0


class Competitor(BaseModel):
    """An existing competitive hotel in the base year."""

    name: str
    rooms: int = Field(gt=0)
    occupancy: float = Field(ge=0.0, le=1.0, description="Base-year occupancy")
    segmentation: dict[str, float] = Field(description="Share of room nights by segment, e.g. {'leisure': 0.6, 'meeting': 0.25, 'commercial': 0.15}; must sum to 1")
    fraction_open: float = Field(default=1.0, ge=0.0, le=1.0, description="Share of the base year the hotel was open (for HARC)")
    competitive_weight: float = Field(default=1.0, gt=0.0, le=1.0, description="1.0 for a primary competitor; less for a secondary one")
    adr: Optional[float] = Field(default=None, description="Base-year blended ADR, used to derive segment ADRs when market segment ADRs are not given")


class NewSupply(BaseModel):
    """A competitive hotel that opens during the projection period."""

    name: str
    rooms: int = Field(gt=0)
    open_year: int = Field(ge=1, description="First projection year with rooms available")
    first_year_fraction: float = Field(default=1.0, ge=0.0, le=1.0, description="Share of the opening year the hotel is open")
    competitive_weight: float = Field(default=1.0, gt=0.0, le=1.0)
    penetration: dict[str, float] = Field(description="Penetration index by segment once open, e.g. {'leisure': 1.1, 'meeting': 0.9}")


class SubjectHotel(BaseModel):
    """The proposed property."""

    rooms: int = Field(gt=0)
    opening_fraction: list[float] = Field(description="Share of each projection year the subject is open, e.g. [0.5, 1, 1, 1, 1]")
    penetration: dict[str, list[float]] = Field(description="Penetration index per segment per year, e.g. {'leisure': [0.8, 1.0, 1.15, 1.2, 1.2]}")
    adr_index: dict[str, float] = Field(default_factory=dict, description="Subject ADR relative to the market segment ADR at stabilisation, e.g. {'leisure': 1.25}; default 1.0")
    adr_ramp: Optional[list[float]] = Field(default=None, description="Optional discount to the stabilised ADR index by year, e.g. [0.9, 0.95, 1, 1, 1]")


@dataclass
class BaseYearRow:
    name: str
    effective_rooms: float
    fair_share: float
    room_nights: float
    market_share: float
    penetration_by_segment: dict
    room_nights_by_segment: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProjectionRow:
    year: int
    total_effective_rooms: float
    market_demand_by_segment: dict
    market_occupancy: float
    subject_effective_rooms: float
    subject_fair_share: float
    subject_room_nights_by_segment: dict
    subject_room_nights: float
    subject_market_share: float
    subject_overall_penetration: float
    subject_occupancy: float
    segment_adr: dict
    subject_adr: float
    subject_revpar: float
    rooms_revenue: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MarketStudyResult:
    segments: list[str]
    base_year: list[BaseYearRow]
    base_year_demand_by_segment: dict
    base_year_market_occupancy: float
    projection: list[ProjectionRow]
    stabilised_year: int | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "segments": self.segments,
            "base_year": [r.to_dict() for r in self.base_year],
            "base_year_demand_by_segment": self.base_year_demand_by_segment,
            "base_year_market_occupancy": self.base_year_market_occupancy,
            "projection": [r.to_dict() for r in self.projection],
            "stabilised_year": self.stabilised_year,
            "occupancy_by_year": [r.subject_occupancy for r in self.projection],
            "adr_by_year": [r.subject_adr for r in self.projection],
            "warnings": self.warnings,
        }


def market_study(
    competitors: list[Competitor],
    subject: SubjectHotel,
    segment_growth: dict[str, float | list[float]],
    base_segment_adr: dict[str, float],
    years: int,
    unaccommodated_demand: Optional[dict[str, float]] = None,
    induced_demand: Optional[dict[str, list[float]]] = None,
    new_supply: Optional[list[NewSupply]] = None,
    adr_inflation: float = 0.03,
    max_occupancy: float | None = None,
) -> MarketStudyResult:
    """Run the built-up room-night analysis and ADR forecast.

    ``segment_growth`` is a rate per segment (one value or one per year).
    ``unaccommodated_demand`` is latent demand per segment as a share of the
    base-year accommodated room nights; it is added to market demand from year
    one and grows with the segment. ``induced_demand`` is room nights per
    segment per projection year. ``base_segment_adr`` is the market ADR per
    segment in base-year currency; it grows at ``adr_inflation``.
    """
    if not competitors:
        raise ValueError("at least one competitor is required")
    if years <= 0:
        raise ValueError("years must be positive")
    segments = list(base_segment_adr.keys())
    if not segments:
        raise ValueError("base_segment_adr must name at least one segment")
    for c in competitors:
        total = sum(c.segmentation.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"{c.name}: segmentation shares sum to {total:.3f}, not 1")
        unknown = set(c.segmentation) - set(segments)
        if unknown:
            raise ValueError(f"{c.name}: segments {sorted(unknown)} are not in base_segment_adr")
    if len(subject.opening_fraction) != years:
        raise ValueError(f"subject.opening_fraction needs {years} entries")
    for s in segments:
        if s not in subject.penetration or len(subject.penetration[s]) != years:
            raise ValueError(f"subject.penetration['{s}'] needs {years} entries")
    if subject.adr_ramp is not None and len(subject.adr_ramp) != years:
        raise ValueError(f"subject.adr_ramp needs {years} entries")
    unacc = unaccommodated_demand or {}
    induced = induced_demand or {}
    for s, series in induced.items():
        if len(series) != years:
            raise ValueError(f"induced_demand['{s}'] needs {years} entries")
    growth = {s: _expand(segment_growth.get(s, 0.0), years, f"segment_growth['{s}']") for s in segments}
    warnings: list[str] = []

    # ---- base year
    base_rows: list[BaseYearRow] = []
    eff_rooms = {c.name: c.rooms * c.fraction_open * c.competitive_weight for c in competitors}
    total_eff = sum(eff_rooms.values())
    rn_by_comp: dict[str, dict[str, float]] = {}
    demand = {s: 0.0 for s in segments}
    for c in competitors:
        harc = c.rooms * c.fraction_open
        rn = {s: harc * DAYS * c.occupancy * c.segmentation.get(s, 0.0) for s in segments}
        rn_by_comp[c.name] = rn
        for s in segments:
            demand[s] += rn[s]
    total_demand = sum(demand.values())
    for c in competitors:
        rn = rn_by_comp[c.name]
        fair = eff_rooms[c.name] / total_eff
        pen = {s: ((rn[s] / demand[s]) / fair if demand[s] > 0 and fair > 0 else 0.0) for s in segments}
        base_rows.append(BaseYearRow(
            name=c.name, effective_rooms=eff_rooms[c.name], fair_share=fair, room_nights=sum(rn.values()),
            market_share=(sum(rn.values()) / total_demand) if total_demand else 0.0,
            penetration_by_segment=pen, room_nights_by_segment=rn,
        ))
    base_market_occ = total_demand / (total_eff * DAYS) if total_eff else 0.0
    # competitors keep their base-year indices through the projection
    comp_pen = {r.name: r.penetration_by_segment for r in base_rows}

    # ---- projection
    rows: list[ProjectionRow] = []
    stabilised_year = None
    prev_occ = None
    for t in range(1, years + 1):
        gf = {s: _cumulative_growth(growth[s], t) for s in segments}
        market_demand = {}
        for s in segments:
            base = demand[s] * (1.0 + unacc.get(s, 0.0))
            ind = induced.get(s, [0.0] * years)[t - 1]
            market_demand[s] = base * gf[s] + ind
        # supply this year
        supply: list[tuple[str, float, dict[str, float]]] = [(c.name, eff_rooms[c.name], comp_pen[c.name]) for c in competitors]
        for ns in new_supply or []:
            if t < ns.open_year:
                continue
            frac = ns.first_year_fraction if t == ns.open_year else 1.0
            supply.append((ns.name, ns.rooms * frac * ns.competitive_weight, {s: ns.penetration.get(s, 1.0) for s in segments}))
        subj_eff = subject.rooms * subject.opening_fraction[t - 1]
        subj_pen = {s: subject.penetration[s][t - 1] for s in segments}
        supply.append(("subject", subj_eff, subj_pen))
        tot_eff = sum(e for _, e, _ in supply)
        subj_rn = {}
        for s in segments:
            weights = {n: e * p.get(s, 1.0) for n, e, p in supply}
            wsum = sum(weights.values())
            subj_rn[s] = market_demand[s] * (weights["subject"] / wsum if wsum else 0.0)
        subj_total = sum(subj_rn.values())
        available = subj_eff * DAYS
        occ = subj_total / available if available else 0.0
        if max_occupancy is not None and occ > max_occupancy:
            scale = max_occupancy / occ
            subj_rn = {s: v * scale for s, v in subj_rn.items()}
            subj_total *= scale
            occ = max_occupancy
            warnings.append(f"year {t}: projected occupancy capped at {max_occupancy:.0%}; excess demand is left unaccommodated")
        fair = subj_eff / tot_eff if tot_eff else 0.0
        mkt_total = sum(market_demand.values())
        share = subj_total / mkt_total if mkt_total else 0.0
        infl = (1.0 + adr_inflation) ** t
        ramp = subject.adr_ramp[t - 1] if subject.adr_ramp else 1.0
        seg_adr = {s: base_segment_adr[s] * infl * subject.adr_index.get(s, 1.0) * ramp for s in segments}
        adr = sum(subj_rn[s] * seg_adr[s] for s in segments) / subj_total if subj_total else 0.0
        revpar = adr * occ
        rows.append(ProjectionRow(
            year=t, total_effective_rooms=tot_eff, market_demand_by_segment=market_demand,
            market_occupancy=mkt_total / (tot_eff * DAYS) if tot_eff else 0.0,
            subject_effective_rooms=subj_eff, subject_fair_share=fair, subject_room_nights_by_segment=subj_rn,
            subject_room_nights=subj_total, subject_market_share=share,
            subject_overall_penetration=(share / fair) if fair else 0.0, subject_occupancy=occ,
            segment_adr=seg_adr, subject_adr=adr, subject_revpar=revpar, rooms_revenue=subj_total * adr,
        ))
        if stabilised_year is None and prev_occ is not None and abs(occ - prev_occ) < 0.005 and subject.opening_fraction[t - 1] >= 1.0:
            stabilised_year = t
        prev_occ = occ
        if occ > 0.80:
            warnings.append(f"year {t}: projected occupancy {occ:.1%} is above 80%; check the penetration indices against the comp set")
    stabilised = rows[-1]
    if stabilised.subject_overall_penetration > 1.3:
        warnings.append("stabilised overall penetration above 1.3x fair share is rare; justify with product and brand evidence")
    return MarketStudyResult(segments=segments, base_year=base_rows, base_year_demand_by_segment=demand,
                             base_year_market_occupancy=base_market_occ, projection=rows,
                             stabilised_year=stabilised_year, warnings=sorted(set(warnings)))


def _expand(value: float | list[float], years: int, name: str) -> list[float]:
    if isinstance(value, (int, float)):
        return [float(value)] * years
    vals = [float(v) for v in value]
    if len(vals) != years:
        raise ValueError(f"{name} needs {years} entries")
    return vals


def _cumulative_growth(rates: list[float], t: int) -> float:
    f = 1.0
    for r in rates[:t]:
        f *= 1.0 + r
    return f
