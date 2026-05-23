import logging
import sys
import os
import json
from datetime import datetime, date, timedelta
from sqlalchemy import desc

# Add parent directory to path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.schemas import HistoricalEvent, GoldPrice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("seed_historical_events")

# List of major world events
EVENTS_DATA = [
    # Category: War & Geopolitics
    {
        "event_date": "2001-09-11",
        "event_type": "war",
        "title": "September 11 Terrorist Attacks",
        "description": "Al-Qaeda hijackers crash planes into the World Trade Center and the Pentagon, triggering the War on Terror.",
        "impact_level": 5,
        "tags": ["terrorism", "war", "us", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2001-10-07",
        "event_type": "war",
        "title": "US Invasion of Afghanistan Begins",
        "description": "US and allied forces launch Operation Enduring Freedom in Afghanistan to dismantle Al-Qaeda.",
        "impact_level": 4,
        "tags": ["war", "afghanistan", "us", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2003-03-20",
        "event_type": "war",
        "title": "US Invasion of Iraq",
        "description": "US-led coalition invades Iraq, deposing Saddam Hussein and destabilizing the Middle East.",
        "impact_level": 5,
        "tags": ["war", "iraq", "middle_east", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2006-07-12",
        "event_type": "war",
        "title": "Israel-Lebanon War Begins",
        "description": "A 34-day military conflict in Lebanon, Northern Israel and the Golan Heights.",
        "impact_level": 3,
        "tags": ["war", "israel", "lebanon", "middle_east"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-08-08",
        "event_type": "war",
        "title": "Russia-Georgia War",
        "description": "Armed conflict between Russia and Georgia over the breakaway regions of South Ossetia and Abkhazia.",
        "impact_level": 3,
        "tags": ["war", "russia", "georgia", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-03-19",
        "event_type": "war",
        "title": "NATO Intervention in Libya",
        "description": "NATO coalition begins a military intervention in Libya to implement a UN Security Council resolution.",
        "impact_level": 3,
        "tags": ["war", "libya", "nato", "africa"],
        "source": "manual_curation"
    },
    {
        "event_date": "2014-02-20",
        "event_type": "war",
        "title": "Russian Annexation of Crimea Begins",
        "description": "Russian forces invade and subsequently annex the Crimean Peninsula from Ukraine.",
        "impact_level": 4,
        "tags": ["war", "russia", "ukraine", "crimea", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2014-06-10",
        "event_type": "war",
        "title": "ISIS Captures Mosul",
        "description": "The Islamic State of Iraq and the Levant captures Mosul, establishing a self-proclaimed caliphate.",
        "impact_level": 3,
        "tags": ["war", "isis", "iraq", "middle_east"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-09-30",
        "event_type": "war",
        "title": "Russian Intervention in Syria",
        "description": "Russia launches air strikes and military operations in Syria to support the Assad regime.",
        "impact_level": 3,
        "tags": ["war", "russia", "syria", "middle_east"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-01-03",
        "event_type": "war",
        "title": "US Assassination of Qasem Soleimani",
        "description": "US drone strike kills Iranian general Qasem Soleimani in Baghdad, spiking US-Iran tensions.",
        "impact_level": 4,
        "tags": ["conflict", "iran", "us", "assassination"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-02-24",
        "event_type": "war",
        "title": "Russia Invades Ukraine",
        "description": "Russia launches a full-scale invasion of Ukraine, triggering the largest war in Europe since WWII and widespread sanctions.",
        "impact_level": 5,
        "tags": ["war", "russia", "ukraine", "sanctions", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2023-10-07",
        "event_type": "war",
        "title": "Hamas Attacks Israel",
        "description": "Hamas launches a surprise attack on Israel, triggering the Israel-Hamas war and rising regional proxy conflicts.",
        "impact_level": 5,
        "tags": ["war", "israel", "gaza", "middle_east"],
        "source": "manual_curation"
    },
    {
        "event_date": "2024-04-13",
        "event_type": "war",
        "title": "Iran Attacks Israel with Drones/Missiles",
        "description": "Iran launches direct retaliatory strikes against Israel, escalating proxy warfare into direct conflict.",
        "impact_level": 4,
        "tags": ["war", "iran", "israel", "escalation"],
        "source": "manual_curation"
    },
    {
        "event_date": "2024-10-01",
        "event_type": "war",
        "title": "Israel Launches Ground Operation in Lebanon",
        "description": "Israel begins ground incursions into Lebanon targeting Hezbollah, escalating the regional conflict.",
        "impact_level": 4,
        "tags": ["war", "israel", "lebanon", "hezbollah"],
        "source": "manual_curation"
    },

    # Category: Monetary Policy
    {
        "event_date": "2004-06-30",
        "event_type": "monetary_policy",
        "title": "Fed Begins Rate Tightening Cycle",
        "description": "Federal Reserve raises target rate from historical low of 1.00% to 1.25%, starting a multi-year hike cycle.",
        "impact_level": 3,
        "tags": ["interest_rates", "fed", "tightening"],
        "source": "manual_curation"
    },
    {
        "event_date": "2006-06-29",
        "event_type": "monetary_policy",
        "title": "Fed Raises Rates to 5.25% Peak",
        "description": "Federal Reserve raises rates to 5.25%, marking the peak of the 2004-2006 hiking cycle.",
        "impact_level": 3,
        "tags": ["interest_rates", "fed", "peak_rate"],
        "source": "manual_curation"
    },
    {
        "event_date": "2007-09-18",
        "event_type": "monetary_policy",
        "title": "Fed Begins Emergency Rate Cuts",
        "description": "Fed cuts discount and funds rates by 50bps, signaling the start of monetary easing in response to subprime distress.",
        "impact_level": 4,
        "tags": ["interest_rates", "fed", "easing", "cuts"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-11-25",
        "event_type": "monetary_policy",
        "title": "Fed Announces QE1",
        "description": "Federal Reserve launches Quantitative Easing, purchasing $600 billion in mortgage-backed securities (MBS).",
        "impact_level": 5,
        "tags": ["fed", "qe", "liquidity", "monetary_expansion"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-12-16",
        "event_type": "monetary_policy",
        "title": "Fed Cuts Rates to Zero Range",
        "description": "Federal Reserve slashes rates to a record range of 0% to 0.25% (Zero Lower Bound) during the depth of the GFC.",
        "impact_level": 5,
        "tags": ["fed", "interest_rates", "zlb", "cuts"],
        "source": "manual_curation"
    },
    {
        "event_date": "2010-11-03",
        "event_type": "monetary_policy",
        "title": "Fed Announces QE2",
        "description": "Federal Reserve announces second round of Quantitative Easing to purchase $600 billion of longer-term Treasuries.",
        "impact_level": 4,
        "tags": ["fed", "qe", "liquidity", "monetary_expansion"],
        "source": "manual_curation"
    },
    {
        "event_date": "2012-09-13",
        "event_type": "monetary_policy",
        "title": "Fed Announces QE3",
        "description": "Fed initiates open-ended asset purchase program of $85 billion/month, pledging to buy until employment improves.",
        "impact_level": 4,
        "tags": ["fed", "qe", "monetary_expansion"],
        "source": "manual_curation"
    },
    {
        "event_date": "2013-05-22",
        "event_type": "monetary_policy",
        "title": "Bernanke Easing Taper Hint (Taper Tantrum)",
        "description": "Fed Chairman Ben Bernanke suggests the Fed may begin tapering its monthly asset purchases, causing global market yields to spike.",
        "impact_level": 4,
        "tags": ["fed", "taper", "bond_yields", "market_panic"],
        "source": "manual_curation"
    },
    {
        "event_date": "2013-12-18",
        "event_type": "monetary_policy",
        "title": "Fed Officially Announces QE3 Tapering",
        "description": "Federal Reserve announces it will reduce asset purchases from $85 billion to $75 billion per month starting in Jan 2014.",
        "impact_level": 3,
        "tags": ["fed", "taper", "monetary_tightening"],
        "source": "manual_curation"
    },
    {
        "event_date": "2014-10-29",
        "event_type": "monetary_policy",
        "title": "Fed Ends QE3 Asset Purchases",
        "description": "Federal Reserve formally concludes its historic third quantitative easing program.",
        "impact_level": 3,
        "tags": ["fed", "qe", "monetary_tightening"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-12-16",
        "event_type": "monetary_policy",
        "title": "Fed Raises Rates First Time in 9 Years",
        "description": "Federal Reserve increases federal funds target range to 0.25%-0.50%, ending a 7-year zero-rate era.",
        "impact_level": 4,
        "tags": ["fed", "interest_rates", "rate_hike"],
        "source": "manual_curation"
    },
    {
        "event_date": "2019-07-31",
        "event_type": "monetary_policy",
        "title": "Fed Cuts Rates First Time Since 2008",
        "description": "Federal Reserve lowers rates by 25bps as insurance against global economic weakness, starting a mid-cycle adjustment.",
        "impact_level": 3,
        "tags": ["fed", "interest_rates", "rate_cut"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-03-15",
        "event_type": "monetary_policy",
        "title": "Emergency Fed Rate Cut to Zero + QE",
        "description": "Federal Reserve slashes rates to 0.00%-0.25% in a Sunday emergency move and launches $700 billion asset purchases to stabilize economy from COVID.",
        "impact_level": 5,
        "tags": ["fed", "rate_cut", "qe", "covid", "emergency"],
        "source": "manual_curation"
    },
    {
        "event_date": "2021-11-03",
        "event_type": "monetary_policy",
        "title": "Fed Announces QE Tapering",
        "description": "Fed announces it will begin reducing its $120B/month bond buying program, signaling future rate hikes.",
        "impact_level": 3,
        "tags": ["fed", "taper", "monetary_tightening"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-03-16",
        "event_type": "monetary_policy",
        "title": "Fed Launches Historic Rate Hiking Cycle",
        "description": "Fed raises rates by 25bps to combat surging inflation, starting the fastest tightening cycle in 40 years.",
        "impact_level": 4,
        "tags": ["fed", "interest_rates", "rate_hike", "inflation"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-06-15",
        "event_type": "monetary_policy",
        "title": "Fed Hikes Rates by 75bps",
        "description": "Fed delivers a giant 75bps rate hike, its largest since 1994, in an aggressive attempt to curb inflation.",
        "impact_level": 4,
        "tags": ["fed", "interest_rates", "rate_hike", "inflation"],
        "source": "manual_curation"
    },
    {
        "event_date": "2023-07-26",
        "event_type": "monetary_policy",
        "title": "Fed Raises Rates to 5.25%-5.50% Peak",
        "description": "Fed raises rates by 25bps to reach a 22-year high, marking the eventual peak of the hiking cycle.",
        "impact_level": 4,
        "tags": ["fed", "interest_rates", "rate_peak"],
        "source": "manual_curation"
    },
    {
        "event_date": "2024-09-18",
        "event_type": "monetary_policy",
        "title": "Fed Pivot: 50bps Easing Cycle Start",
        "description": "Federal Reserve cuts interest rates by 50bps, signaling confidence in inflation falling and starting a policy easing cycle.",
        "impact_level": 4,
        "tags": ["fed", "rate_cut", "pivot", "easing"],
        "source": "manual_curation"
    },

    # Category: Economic Crisis
    {
        "event_date": "2007-08-09",
        "event_type": "economic_crisis",
        "title": "BNP Paribas Freezes Subprime Mortgage Funds",
        "description": "French bank BNP Paribas freezes three investment funds, marking the official onset of the global subprime liquidity crisis.",
        "impact_level": 4,
        "tags": ["liquidity", "subprime", "financial_crisis"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-03-16",
        "event_type": "economic_crisis",
        "title": "Bear Stearns Collapse and JPMorgan Rescue",
        "description": "JPMorgan Chase acquires investment bank Bear Stearns for $2 a share in a government-backed rescue deal.",
        "impact_level": 4,
        "tags": ["bank_failure", "liquidity", "bailout"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-09-15",
        "event_type": "economic_crisis",
        "title": "Lehman Brothers Bankruptcy",
        "description": "Lehman Brothers files for Chapter 11 bankruptcy, triggering the worst global financial panic since the Great Depression.",
        "impact_level": 5,
        "tags": ["financial_crisis", "bankruptcy", "banking_collapse", "gfc"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-10-03",
        "event_type": "economic_crisis",
        "title": "Congress Passes $700 Billion TARP Bailout",
        "description": "US passes Troubled Asset Relief Program to purchase toxic assets from financial institutions to prevent systemic collapse.",
        "impact_level": 4,
        "tags": ["bailout", "us", "stimulus", "government_intervention"],
        "source": "manual_curation"
    },
    {
        "event_date": "2009-03-09",
        "event_type": "economic_crisis",
        "title": "S&P 500 Hits Great Recession Bottom",
        "description": "S&P 500 index bottoms out at a closing low of 676.53 during the Financial Crisis.",
        "impact_level": 4,
        "tags": ["stocks", "bear_market", "bottom"],
        "source": "manual_curation"
    },
    {
        "event_date": "2010-05-02",
        "event_type": "economic_crisis",
        "title": "Greece Receives First IMF/EU Bailout",
        "description": "Eurozone nations and the IMF approve a €110 billion bailout package for Greece, starting the European Debt Crisis.",
        "impact_level": 4,
        "tags": ["debt_crisis", "europe", "greece", "bailout"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-08-05",
        "event_type": "economic_crisis",
        "title": "S&P Downgrades United States Credit Rating",
        "description": "Standard & Poor's cuts the credit rating of the US from AAA to AA+ following the debt-ceiling standoff.",
        "impact_level": 5,
        "tags": ["us", "credit_downgrade", "debt_ceiling"],
        "source": "manual_curation"
    },
    {
        "event_date": "2012-06-09",
        "event_type": "economic_crisis",
        "title": "Spain Requests Bank Bailout",
        "description": "Spain asks Eurozone for up to €100 billion to recapitalize its struggling banks during the European debt crisis.",
        "impact_level": 3,
        "tags": ["bailout", "spain", "europe", "sovereign_debt"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-08-24",
        "event_type": "economic_crisis",
        "title": "China's 'Black Monday' Stock Market Crash",
        "description": "Shanghai stock index drops 8.5% in one day, triggering worldwide stock selloffs and commodity drops.",
        "impact_level": 4,
        "tags": ["stocks", "market_crash", "china"],
        "source": "manual_curation"
    },
    {
        "event_date": "2018-12-24",
        "event_type": "economic_crisis",
        "title": "Christmas Eve Stock Market Crash",
        "description": "US indices suffer worst Christmas Eve fall on record amid concerns over Fed tightening and political gridlock.",
        "impact_level": 3,
        "tags": ["market_crash", "stocks", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-03-09",
        "event_type": "economic_crisis",
        "title": "Oil Price War + Covid Market Crash",
        "description": "Oil prices crash 30% alongside a massive global equity selloff as COVID panic sets in.",
        "impact_level": 5,
        "tags": ["market_crash", "oil", "covid"],
        "source": "manual_curation"
    },
    {
        "event_date": "2023-03-10",
        "event_type": "economic_crisis",
        "title": "Silicon Valley Bank Collapse",
        "description": "Silicon Valley Bank is shut down by regulators, marking the second-largest bank failure in US history and sparking banking sector panic.",
        "impact_level": 5,
        "tags": ["bank_failure", "banking_crisis", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2023-03-15",
        "event_type": "economic_crisis",
        "title": "Credit Suisse Swiss Bailout/Rescue",
        "description": "Swiss National Bank provides emergency liquidity to Credit Suisse, which is later forced into a merger with UBS.",
        "impact_level": 4,
        "tags": ["bank_failure", "europe", "switzerland"],
        "source": "manual_curation"
    },

    # Category: Pandemic
    {
        "event_date": "2020-01-20",
        "event_type": "pandemic",
        "title": "First COVID-19 Cases Confirmed in US",
        "description": "CDC confirms the first laboratory-proven infection of COVID-19 in the United States.",
        "impact_level": 3,
        "tags": ["pandemic", "covid", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-03-11",
        "event_type": "pandemic",
        "title": "WHO Declares COVID-19 Global Pandemic",
        "description": "World Health Organization formally declares COVID-19 outbreak a global pandemic, prompting lockdowns.",
        "impact_level": 5,
        "tags": ["pandemic", "covid", "lockdown", "global"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-03-23",
        "event_type": "pandemic",
        "title": "US Lockdowns & Stock Market Bottom",
        "description": "Lockdowns spread across US states; Federal Reserve goes 'unlimited QE' to stem massive equity declines.",
        "impact_level": 5,
        "tags": ["pandemic", "covid", "market_bottom", "lockdown"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-12-14",
        "event_type": "pandemic",
        "title": "First Covid Vaccines Administered in US",
        "description": "US launches historic immunization drive using Pfizer/BioNTech vaccine, sparking recovery hopes.",
        "impact_level": 3,
        "tags": ["vaccine", "covid", "recovery"],
        "source": "manual_curation"
    },
    {
        "event_date": "2021-11-26",
        "event_type": "pandemic",
        "title": "Omicron Variant Discovered",
        "description": "WHO designates Omicron as a variant of concern, sparking brief market panic and travel bans.",
        "impact_level": 3,
        "tags": ["covid", "variant", "market_panic"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-12-07",
        "event_type": "pandemic",
        "title": "China Abandons Zero-COVID Policy",
        "description": "China drastically eases strict lockdowns and testing restrictions, starting the re-opening of the world's second-largest economy.",
        "impact_level": 4,
        "tags": ["china", "reopening", "covid"],
        "source": "manual_curation"
    },

    # Category: Trade & Sanctions
    {
        "event_date": "2018-03-22",
        "event_type": "trade",
        "title": "Trump Announces Tariffs on China",
        "description": "President Trump signs memorandum targeting $60 billion of Chinese imports with tariffs, escalating trade tensions.",
        "impact_level": 4,
        "tags": ["tariffs", "us_china", "trade_war"],
        "source": "manual_curation"
    },
    {
        "event_date": "2018-07-06",
        "event_type": "trade",
        "title": "US-China Trade War Officially Begins",
        "description": "US tariffs on $34 billion of Chinese imports take effect; China retaliates with matching tariffs.",
        "impact_level": 4,
        "tags": ["trade_war", "us", "china", "tariffs"],
        "source": "manual_curation"
    },
    {
        "event_date": "2019-08-05",
        "event_type": "trade",
        "title": "China Devalues Yuan Past 7 per USD",
        "description": "China lets yuan drop past 7 to the USD for the first time in a decade, prompting US to label China a currency manipulator.",
        "impact_level": 4,
        "tags": ["currency", "china", "yuan", "trade_war"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-01-15",
        "event_type": "trade",
        "title": "US-China Phase One Trade Deal Signed",
        "description": "US and China sign initial trade agreement, temporarily easing trade war tensions.",
        "impact_level": 3,
        "tags": ["trade_deal", "us_china", "deescalation"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-02-26",
        "event_type": "trade",
        "title": "SWIFT Sanctions Imposed on Russia",
        "description": "Western nations agree to block selected Russian banks from the SWIFT global payments system, freezing CBR reserves.",
        "impact_level": 5,
        "tags": ["sanctions", "russia", "swift", "geopolitical_warfare"],
        "source": "manual_curation"
    },

    # Category: Inflation
    {
        "event_date": "2021-05-12",
        "event_type": "inflation",
        "title": "US CPI Hits 4.2% (13-Year High)",
        "description": "US consumer prices jump 4.2% in April, the largest increase since September 2008, signaling pandemic supply chain inflation.",
        "impact_level": 4,
        "tags": ["inflation", "cpi", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2021-11-10",
        "event_type": "inflation",
        "title": "US CPI Surges to 6.2% (30-Year High)",
        "description": "Consumer price index inflation jumps 6.2% YoY, the highest inflation print since 1990.",
        "impact_level": 4,
        "tags": ["inflation", "cpi", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-06-10",
        "event_type": "inflation",
        "title": "US CPI Peaks at 9.1% (40-Year High)",
        "description": "US CPI inflation accelerates to 9.1% in June, the fastest pace of inflation since November 1981, driven by oil and food.",
        "impact_level": 5,
        "tags": ["inflation", "cpi", "peak_inflation"],
        "source": "manual_curation"
    },
    {
        "event_date": "2023-06-13",
        "event_type": "inflation",
        "title": "US CPI Inflation Drops to 3.0%",
        "description": "US annual inflation cools to 3% in May, marking the 11th consecutive month of declines and fueling interest rate pause bets.",
        "impact_level": 3,
        "tags": ["inflation", "cpi", "disinflation"],
        "source": "manual_curation"
    },

    # Category: Elections & Politics
    {
        "event_date": "2008-11-04",
        "event_type": "election",
        "title": "Barack Obama Wins US Presidential Election",
        "description": "Barack Obama is elected the 44th president of the United States amid the worsening financial crisis.",
        "impact_level": 3,
        "tags": ["election", "us", "politics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2016-06-23",
        "event_type": "election",
        "title": "United Kingdom Votes for Brexit",
        "description": "UK electorate votes to leave the European Union in a referendum, sparking major political and economic uncertainty.",
        "impact_level": 5,
        "tags": ["brexit", "uk", "eu", "referendum"],
        "source": "manual_curation"
    },
    {
        "event_date": "2016-11-08",
        "event_type": "election",
        "title": "Donald Trump Wins US Presidency",
        "description": "Donald Trump wins US presidential election in an upset victory, shifting trade and foreign policy expectations.",
        "impact_level": 5,
        "tags": ["election", "us", "politics", "trump"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-11-03",
        "event_type": "election",
        "title": "Joe Biden Wins US Presidency",
        "description": "Joe Biden is elected the 46th president of the United States in a highly contested election.",
        "impact_level": 4,
        "tags": ["election", "us", "politics", "biden"],
        "source": "manual_curation"
    },
    {
        "event_date": "2024-11-05",
        "event_type": "election",
        "title": "Donald Trump Wins 2024 US Election",
        "description": "Donald Trump wins the 2024 US presidential election, gaining control of the presidency and the Senate.",
        "impact_level": 5,
        "tags": ["election", "us", "trump", "politics"],
        "source": "manual_curation"
    },

    # Category: Market Crash
    {
        "event_date": "2010-05-06",
        "event_type": "market_crash",
        "title": "Flash Crash of 2010",
        "description": "Dow Jones Industrial Average drops nearly 1,000 points (about 9%) in minutes before recovering most losses, highlighting high-frequency trading risks.",
        "impact_level": 4,
        "tags": ["crash", "stocks", "liquidity", "flash_crash"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-08-08",
        "event_type": "market_crash",
        "title": "Global Market Sell-off After US Downgrade",
        "description": "World stock markets plummet following S&P's credit rating downgrade of the United States.",
        "impact_level": 5,
        "tags": ["stocks", "crash", "sovereign_rating"],
        "source": "manual_curation"
    },
    {
        "event_date": "2018-02-05",
        "event_type": "market_crash",
        "title": "Volmageddon (VIX Spike)",
        "description": "VIX index experiences its largest-ever one-day increase, wiping out inverse-volatility funds and crashing global stocks.",
        "impact_level": 4,
        "tags": ["volatility", "crash", "stocks", "vix"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-03-12",
        "event_type": "market_crash",
        "title": "COVID Stock Market Crash",
        "description": "US stock market experiences worst one-day fall since 1987 as COVID closures freeze business activity.",
        "impact_level": 5,
        "tags": ["crash", "stocks", "covid"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-09-26",
        "event_type": "market_crash",
        "title": "UK Gilt Market Crisis",
        "description": "UK government bond prices collapse following prime minister Liz Truss's mini-budget, requiring emergency BoE intervention.",
        "impact_level": 4,
        "tags": ["bonds", "uk", "gilt_market", "currency_crisis"],
        "source": "manual_curation"
    },
    {
        "event_date": "2001-11-10",
        "event_type": "trade",
        "title": "China Joins World Trade Organization (WTO)",
        "description": "China officially joins the WTO, integrating into the global economy and launching its rise as an industrial powerhouse.",
        "impact_level": 4,
        "tags": ["china", "wto", "globalization", "trade"],
        "source": "manual_curation"
    },
    {
        "event_date": "2002-01-01",
        "event_type": "economic_crisis",
        "title": "Euro Currency Notes and Coins Introduced",
        "description": "Euro notes and coins enter circulation in twelve EU member states, establishing a major competitor to the US dollar.",
        "impact_level": 3,
        "tags": ["euro", "europe", "currency"],
        "source": "manual_curation"
    },
    {
        "event_date": "2002-11-16",
        "event_type": "pandemic",
        "title": "SARS Outbreak Begins in China",
        "description": "Severe Acute Respiratory Syndrome (SARS) outbreak begins in Guangdong province, China, spreading globally over the following months.",
        "impact_level": 3,
        "tags": ["pandemic", "sars", "china", "health"],
        "source": "manual_curation"
    },
    {
        "event_date": "2003-12-14",
        "event_type": "war",
        "title": "Saddam Hussein Captured",
        "description": "US forces capture deposed Iraqi President Saddam Hussein near Tikrit, Iraq.",
        "impact_level": 3,
        "tags": ["iraq", "saddam", "war", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2004-03-11",
        "event_type": "war",
        "title": "Madrid Train Bombings",
        "description": "Simultaneous bomb attacks on commuter trains in Madrid kill 191 people and wound over 1,800, leading to a shift in Spanish foreign policy.",
        "impact_level": 3,
        "tags": ["terrorism", "spain", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2004-12-26",
        "event_type": "economic_crisis",
        "title": "Indian Ocean Earthquake and Tsunami",
        "description": "A magnitude 9.1-9.3 earthquake triggers a massive tsunami across the Indian Ocean, causing widespread devastation and humanitarian crisis.",
        "impact_level": 4,
        "tags": ["tsunami", "disaster", "asia"],
        "source": "manual_curation"
    },
    {
        "event_date": "2005-07-07",
        "event_type": "war",
        "title": "London 7/7 Terrorist Bombings",
        "description": "Suicide bombers strike London's public transport system during the morning rush hour, killing 52 people and injuring hundreds.",
        "impact_level": 3,
        "tags": ["terrorism", "uk", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2005-08-29",
        "event_type": "economic_crisis",
        "title": "Hurricane Katrina Hits US Gulf Coast",
        "description": "Hurricane Katrina causes catastrophic damage in New Orleans and the Gulf Coast, disrupting oil refining capacity and driving up energy prices.",
        "impact_level": 4,
        "tags": ["hurricane", "disaster", "us", "oil"],
        "source": "manual_curation"
    },
    {
        "event_date": "2006-10-09",
        "event_type": "war",
        "title": "North Korea Conducts First Nuclear Test",
        "description": "North Korea announces its first successful underground nuclear test, sparking international condemnation and sanctions.",
        "impact_level": 4,
        "tags": ["nuclear", "north_korea", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2007-01-01",
        "event_type": "economic_crisis",
        "title": "Romania and Bulgaria Join the EU",
        "description": "Expansion of the European Union eastward, incorporating new markets and labor supply.",
        "impact_level": 2,
        "tags": ["eu", "expansion", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2007-04-02",
        "event_type": "economic_crisis",
        "title": "New Century Financial Files for Bankruptcy",
        "description": "Major US subprime mortgage lender files for Chapter 11, signaling systemic cracks in the housing market.",
        "impact_level": 3,
        "tags": ["subprime", "bankruptcy", "housing"],
        "source": "manual_curation"
    },
    {
        "event_date": "2007-06-21",
        "event_type": "monetary_policy",
        "title": "Hawkish ECB Raises Rates to 4.0%",
        "description": "European Central Bank raises its benchmark interest rate to 4.0% to curb rising Eurozone inflation.",
        "impact_level": 3,
        "tags": ["ecb", "interest_rates", "tightening"],
        "source": "manual_curation"
    },
    {
        "event_date": "2007-10-11",
        "event_type": "market_crash",
        "title": "US Dow Jones Peaks Before Financial Crisis",
        "description": "The Dow Jones Industrial Average peaks at 14,164.53 before entering a catastrophic bear market.",
        "impact_level": 4,
        "tags": ["stocks", "peak", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2007-12-01",
        "event_type": "economic_crisis",
        "title": "US Enters Great Recession",
        "description": "The National Bureau of Economic Research marks this month as the official start of the 18-month-long Great Recession.",
        "impact_level": 4,
        "tags": ["recession", "us", "macroeconomy"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-01-22",
        "event_type": "monetary_policy",
        "title": "Fed Emergency 75bps Rate Cut",
        "description": "In a rare inter-meeting move, the Federal Reserve slashes rates by 75bps to 3.50% to arrest a worldwide stock selloff.",
        "impact_level": 4,
        "tags": ["fed", "rate_cut", "emergency"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-07-11",
        "event_type": "economic_crisis",
        "title": "Crude Oil Price Peaks at $147.27",
        "description": "Brent crude oil reaches an all-time high of $147.27 per barrel, contributing to high inflation concerns before crashing.",
        "impact_level": 4,
        "tags": ["oil", "commodity", "peak"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-09-07",
        "event_type": "economic_crisis",
        "title": "US Government Nationalizes Fannie Mae and Freddie Mac",
        "description": "Federal Housing Finance Agency places mortgage giants Fannie Mae and Freddie Mac into government conservatorship.",
        "impact_level": 4,
        "tags": ["housing", "nationalization", "bailout"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-09-17",
        "event_type": "economic_crisis",
        "title": "US Fed Rescues AIG with $85 Billion Bailout",
        "description": "Federal Reserve board authorizes $85 billion loan to prevent the collapse of insurance giant American International Group (AIG).",
        "impact_level": 4,
        "tags": ["bailout", "aig", "financial_crisis"],
        "source": "manual_curation"
    },
    {
        "event_date": "2008-10-08",
        "event_type": "monetary_policy",
        "title": "Coordinated Global Central Bank Rate Cuts",
        "description": "Fed, ECB, BoE, and other major central banks cut interest rates simultaneously in an unprecedented emergency response.",
        "impact_level": 5,
        "tags": ["fed", "ecb", "emergency", "cuts"],
        "source": "manual_curation"
    },
    {
        "event_date": "2009-02-17",
        "event_type": "economic_crisis",
        "title": "US Passes $787 Billion Recovery Act",
        "description": "President Obama signs the American Recovery and Reinvestment Act of 2009, a massive fiscal stimulus package.",
        "impact_level": 4,
        "tags": ["stimulus", "us", "fiscal"],
        "source": "manual_curation"
    },
    {
        "event_date": "2009-04-27",
        "event_type": "pandemic",
        "title": "WHO Declares H1N1 Swine Flu Public Health Emergency",
        "description": "World Health Organization declares H1N1 influenza a public health emergency of international concern.",
        "impact_level": 3,
        "tags": ["pandemic", "h1n1", "health"],
        "source": "manual_curation"
    },
    {
        "event_date": "2009-11-25",
        "event_type": "economic_crisis",
        "title": "Dubai World Debt Moratorium Request",
        "description": "State-owned Dubai World requests a debt standstill, rattling global markets and raising sovereign default worries.",
        "impact_level": 3,
        "tags": ["dubai", "debt", "real_estate"],
        "source": "manual_curation"
    },
    {
        "event_date": "2009-12-08",
        "event_type": "economic_crisis",
        "title": "Fitch Downgrades Greece Credit Rating",
        "description": "Fitch cuts Greek sovereign debt rating to BBB+ with a negative outlook, initiating the Eurozone sovereign debt crisis.",
        "impact_level": 4,
        "tags": ["debt_crisis", "greece", "downgrade"],
        "source": "manual_curation"
    },
    {
        "event_date": "2010-03-15",
        "event_type": "trade",
        "title": "US Accuses China of Currency Manipulation",
        "description": "US lawmakers pressure treasury to label China a currency manipulator, heating up bilateral trade tensions.",
        "impact_level": 3,
        "tags": ["china", "currency", "trade"],
        "source": "manual_curation"
    },
    {
        "event_date": "2010-04-20",
        "event_type": "economic_crisis",
        "title": "Deepwater Horizon Oil Spill Begins",
        "description": "An explosion on BP's Deepwater Horizon drilling rig in the Gulf of Mexico causes the largest marine oil spill in history.",
        "impact_level": 3,
        "tags": ["oil", "disaster", "bp"],
        "source": "manual_curation"
    },
    {
        "event_date": "2010-07-21",
        "event_type": "economic_crisis",
        "title": "US Passes Dodd-Frank Financial Reform Act",
        "description": "President Obama signs the Dodd-Frank Wall Street Reform and Consumer Protection Act into law.",
        "impact_level": 3,
        "tags": ["regulation", "banking", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2010-11-28",
        "event_type": "economic_crisis",
        "title": "Ireland Receives €85 Billion EU/IMF Bailout",
        "description": "European Union and IMF approve a rescue package for Ireland to repair its banking sector.",
        "impact_level": 3,
        "tags": ["bailout", "ireland", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-03-11",
        "event_type": "economic_crisis",
        "title": "Fukushima Earthquake and Nuclear Disaster",
        "description": "A magnitude 9.0 earthquake and tsunami strike Japan, causing the Fukushima Daiichi nuclear disaster and global supply chain disruptions.",
        "impact_level": 4,
        "tags": ["earthquake", "nuclear", "japan"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-05-02",
        "event_type": "war",
        "title": "Osama bin Laden Killed",
        "description": "US Navy SEALs kill Al-Qaeda leader Osama bin Laden in Abbottabad, Pakistan.",
        "impact_level": 4,
        "tags": ["bin_laden", "terrorism", "war", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-05-16",
        "event_type": "economic_crisis",
        "title": "Portugal Receives €78 Billion Bailout",
        "description": "Portugal agrees to a three-year EU/IMF rescue program as borrowing costs become unsustainable.",
        "impact_level": 3,
        "tags": ["bailout", "portugal", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-08-23",
        "event_type": "economic_crisis",
        "title": "Gold Price Hits Record High of $1,917.90",
        "description": "Investors flock to gold amid Eurozone debt worries and US credit downgrade, pushing prices to a then-record high.",
        "impact_level": 5,
        "tags": ["gold", "record_price", "safe_haven"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-09-17",
        "event_type": "economic_crisis",
        "title": "Occupy Wall Street Protests Begin",
        "description": "Protests against economic inequality and the influence of corporations on government start in New York City.",
        "impact_level": 2,
        "tags": ["protest", "us", "inequality"],
        "source": "manual_curation"
    },
    {
        "event_date": "2011-09-21",
        "event_type": "monetary_policy",
        "title": "Fed Launches Operation Twist",
        "description": "Federal Reserve announces plan to purchase longer-term Treasuries while selling shorter-term ones to lower long-term yields.",
        "impact_level": 3,
        "tags": ["fed", "operation_twist", "bonds"],
        "source": "manual_curation"
    },
    {
        "event_date": "2012-07-26",
        "event_type": "monetary_policy",
        "title": "ECB President Draghi Pledges 'Whatever It Takes'",
        "description": "Mario Draghi's speech in London vows the ECB will do 'whatever it takes' to preserve the Euro, immediately calming sovereign bond spreads.",
        "impact_level": 5,
        "tags": ["ecb", "draghi", "eurozone", "bond_market"],
        "source": "manual_curation"
    },
    {
        "event_date": "2012-10-29",
        "event_type": "economic_crisis",
        "title": "Hurricane Sandy Hits US East Coast",
        "description": "Superstorm Sandy shuts down Wall Street for two days and causes massive damage across the Mid-Atlantic states.",
        "impact_level": 3,
        "tags": ["hurricane", "market_halt", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2013-03-16",
        "event_type": "economic_crisis",
        "title": "Cyprus Bailout with Bank 'Bail-in' Confirmed",
        "description": "Cyprus receives a €10 billion bailout featuring an unprecedented levy on large bank depositors.",
        "impact_level": 4,
        "tags": ["cyprus", "bailout", "banking", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2013-04-15",
        "event_type": "market_crash",
        "title": "Gold Suffers Historic Two-Day Crash",
        "description": "Gold prices plunge over 9% in a single session, marking the largest daily drop in three decades as commodities crash.",
        "impact_level": 5,
        "tags": ["gold_crash", "commodities", "bear_market"],
        "source": "manual_curation"
    },
    {
        "event_date": "2013-10-01",
        "event_type": "election",
        "title": "US Government 16-Day Shutdown Begins",
        "description": "Funding disputes over the Affordable Care Act lead to a 16-day federal government shutdown and debt limit worries.",
        "impact_level": 3,
        "tags": ["shutdown", "us", "politics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2014-01-01",
        "event_type": "economic_crisis",
        "title": "Tapering of US Bond Purchases Commences",
        "description": "Federal Reserve reduces its monthly asset purchases to $75 billion, starting the exit from QE3.",
        "impact_level": 3,
        "tags": ["fed", "taper", "monetary_policy"],
        "source": "manual_curation"
    },
    {
        "event_date": "2014-06-05",
        "event_type": "monetary_policy",
        "title": "ECB Cuts Deposit Rate to Negative (-0.1%)",
        "description": "European Central Bank becomes the first major central bank to introduce negative interest rates on commercial deposits.",
        "impact_level": 4,
        "tags": ["ecb", "negative_rates", "easing"],
        "source": "manual_curation"
    },
    {
        "event_date": "2014-07-17",
        "event_type": "war",
        "title": "Malaysia Airlines Flight MH17 Shot Down",
        "description": "MH17 is shot down over eastern Ukraine, dramatically escalating diplomatic conflict and sanctions against Russia.",
        "impact_level": 4,
        "tags": ["malaysia_airlines", "russia", "ukraine", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2014-11-27",
        "event_type": "economic_crisis",
        "title": "OPEC Declines to Cut Oil Production",
        "description": "OPEC keeps output steady despite supply glut, triggering a historic crash in crude oil prices below $50/bbl.",
        "impact_level": 4,
        "tags": ["oil", "opec", "price_crash"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-01-15",
        "event_type": "market_crash",
        "title": "Swiss National Bank Abandons Euro Peg",
        "description": "Swiss central bank unexpectedly drops its cap of 1.20 francs per euro, causing Swiss franc to surge and global currency turmoil.",
        "impact_level": 4,
        "tags": ["swiss_franc", "currency", "central_bank"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-01-22",
        "event_type": "monetary_policy",
        "title": "ECB Launches €1 Trillion Quantitative Easing",
        "description": "ECB announces massive bond-buying program of €60 billion per month to combat deflation and economic stagnation.",
        "impact_level": 4,
        "tags": ["ecb", "qe", "eurozone"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-06-30",
        "event_type": "economic_crisis",
        "title": "Greece Misses IMF Payment",
        "description": "Greece becomes the first developed nation to fail to make a payment to the IMF, raising exit risks from the Eurozone.",
        "impact_level": 4,
        "tags": ["greece", "default", "imf", "debt_crisis"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-08-11",
        "event_type": "trade",
        "title": "China Devalues Renminbi (Yuan)",
        "description": "People's Bank of China devalues the yuan by nearly 2% to support exports, raising currency war concerns.",
        "impact_level": 4,
        "tags": ["yuan", "china", "currency_war"],
        "source": "manual_curation"
    },
    {
        "event_date": "2015-11-13",
        "event_type": "war",
        "title": "Paris Terrorist Attacks",
        "description": "Coordinated Islamic State terrorist attacks in Paris kill 130 people, leading to state of emergency in France.",
        "impact_level": 3,
        "tags": ["terrorism", "france", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "2016-01-29",
        "event_type": "monetary_policy",
        "title": "Bank of Japan Introduces Negative Interest Rates",
        "description": "BOJ surprises markets by adopting negative interest rates to spur lending and fight deflation.",
        "impact_level": 4,
        "tags": ["boj", "japan", "negative_rates"],
        "source": "manual_curation"
    },
    {
        "event_date": "2016-11-09",
        "event_type": "market_crash",
        "title": "Trump Election Night Market Volatility",
        "description": "Global futures plunge before staging a dramatic recovery as Donald Trump's presidential victory is confirmed.",
        "impact_level": 4,
        "tags": ["stocks", "election", "volatility"],
        "source": "manual_curation"
    },
    {
        "event_date": "2017-01-20",
        "event_type": "election",
        "title": "Inauguration of Donald Trump",
        "description": "Donald Trump is sworn in as President, starting an era of protectionist trade policies and tax cuts.",
        "impact_level": 3,
        "tags": ["us", "trump", "politics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2017-04-06",
        "event_type": "war",
        "title": "US Launches Missile Strike on Syria",
        "description": "US forces fire Tomahawk missiles at a Syrian airfield in response to a chemical weapons attack, escalating US military involvement.",
        "impact_level": 3,
        "tags": ["syria", "us", "conflict", "middle_east"],
        "source": "manual_curation"
    },
    {
        "event_date": "2017-06-01",
        "event_type": "election",
        "title": "US Announces Withdrawal from Paris Climate Accord",
        "description": "Trump administration announces US exit from the Paris climate agreement, shifting global policy alignment.",
        "impact_level": 2,
        "tags": ["paris_agreement", "us", "politics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2017-12-22",
        "event_type": "economic_crisis",
        "title": "US Tax Cuts and Jobs Act Signed",
        "description": "President Trump signs major tax reform bill cutting corporate tax rate from 35% to 21% and triggering capital inflows.",
        "impact_level": 4,
        "tags": ["tax_cuts", "us", "fiscal_policy"],
        "source": "manual_curation"
    },
    {
        "event_date": "2018-05-08",
        "event_type": "war",
        "title": "US Withdraws from Iran Nuclear Deal (JCPOA)",
        "description": "President Trump announces US withdrawal from the Iran nuclear agreement and reimposition of economic sanctions.",
        "impact_level": 4,
        "tags": ["iran", "sanctions", "nuclear_deal", "geopolitics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2018-09-24",
        "event_type": "trade",
        "title": "US Slaps 10% Tariff on $200B of Chinese Goods",
        "description": "US imposes new round of tariffs on $200 billion worth of Chinese imports, and China retaliates with tariffs on $60 billion of US goods.",
        "impact_level": 4,
        "tags": ["tariffs", "trade_war", "us", "china"],
        "source": "manual_curation"
    },
    {
        "event_date": "2018-10-03",
        "event_type": "monetary_policy",
        "title": "Powell Hawkish Comments on Neutral Rate",
        "description": "Fed Chair Jerome Powell suggests rates are 'a long way from neutral,' triggering a major Q4 market selloff.",
        "impact_level": 4,
        "tags": ["fed", "powell", "tightening"],
        "source": "manual_curation"
    },
    {
        "event_date": "2019-01-04",
        "event_type": "monetary_policy",
        "title": "Powell Pivot: Fed Pledges Patience",
        "description": "Jerome Powell signals flexibility on rate hikes and balance sheet runoff, triggering a powerful market rebound.",
        "impact_level": 4,
        "tags": ["fed", "powell", "pivot"],
        "source": "manual_curation"
    },
    {
        "event_date": "2019-05-05",
        "event_type": "trade",
        "title": "Trump Threatens Tariff Hike to 25%",
        "description": "Trump tweets intention to raise tariffs on Chinese goods from 10% to 25%, breaking trade talks and crashing markets.",
        "impact_level": 3,
        "tags": ["trade_war", "tariffs", "stocks"],
        "source": "manual_curation"
    },
    {
        "event_date": "2019-09-04",
        "event_type": "monetary_policy",
        "title": "Gold Hits Peak of $1,557 on Yield Curve Inversion",
        "description": "Gold prices hit multi-year highs as 2-year and 10-year US Treasury yield curves invert, signaling recession.",
        "impact_level": 4,
        "tags": ["gold", "yield_curve", "inversion", "recession"],
        "source": "manual_curation"
    },
    {
        "event_date": "2019-09-17",
        "event_type": "economic_crisis",
        "title": "US Repo Market Cash Crunch",
        "description": "Secured Overnight Financing Rate (SOFR) spikes to 10% due to corporate tax payments and treasury issuance, prompting Fed liquidity injections.",
        "impact_level": 3,
        "tags": ["repo_market", "liquidity", "fed"],
        "source": "manual_curation"
    },
    {
        "event_date": "2019-12-18",
        "event_type": "election",
        "title": "Donald Trump Impeached First Time",
        "description": "US House of Representatives votes to impeach President Trump on charges of abuse of power and obstruction of Congress.",
        "impact_level": 2,
        "tags": ["impeachment", "us", "politics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-01-03",
        "event_type": "war",
        "title": "Suleimani Assassinated",
        "description": "Spike in geopolitical tensions in the Middle East following the death of Iranian military commander.",
        "impact_level": 4,
        "tags": ["geopolitics", "iran", "conflict"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-01-23",
        "event_type": "pandemic",
        "title": "Wuhan Lockdown Begins",
        "description": "China places Wuhan and other cities under quarantine, signaling the severity of the emerging virus.",
        "impact_level": 4,
        "tags": ["lockdown", "china", "covid"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-02-24",
        "event_type": "market_crash",
        "title": "Global Stock Markets Plunge on COVID Outbreaks",
        "description": "Wall Street suffers major falls as infection counts rise rapidly outside China, signaling a global crisis.",
        "impact_level": 4,
        "tags": ["crash", "stocks", "covid"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-03-09",
        "event_type": "market_crash",
        "title": "Black Monday: US Markets Hit Circuit Breaker",
        "description": "The S&P 500 index plunges 7% at market open, triggering a 15-minute trading halt.",
        "impact_level": 5,
        "tags": ["crash", "circuit_breaker", "covid"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-03-27",
        "event_type": "economic_crisis",
        "title": "US Passes $2.2 Trillion CARES Act",
        "description": "President Trump signs the largest economic stimulus package in US history to mitigate the COVID-19 economic impact.",
        "impact_level": 5,
        "tags": ["stimulus", "us", "fiscal", "covid"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-04-20",
        "event_type": "economic_crisis",
        "title": "WTI Crude Oil Prices Go Negative (-$37.63)",
        "description": "May WTI crude futures drop below zero for the first time in history due to pandemic demand destruction and storage shortages.",
        "impact_level": 5,
        "tags": ["oil", "negative_prices", "commodity", "covid"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-08-06",
        "event_type": "economic_crisis",
        "title": "Gold Price Hits Record High of $2,075",
        "description": "Gold spikes to an all-time high of $2,075 per ounce due to low interest rates and massive global money printing.",
        "impact_level": 5,
        "tags": ["gold", "record", "safe_haven"],
        "source": "manual_curation"
    },
    {
        "event_date": "2020-08-27",
        "event_type": "monetary_policy",
        "title": "Fed Adopts Average Inflation Targeting (AIT)",
        "description": "Fed announces shift to allow inflation to run moderately above 2% to support employment and growth.",
        "impact_level": 3,
        "tags": ["fed", "inflation_targeting", "monetary_policy"],
        "source": "manual_curation"
    },
    {
        "event_date": "2021-01-06",
        "event_type": "election",
        "title": "US Capitol Riot",
        "description": "Protestors storm the US Capitol, disrupting the certification of the 2020 presidential election results.",
        "impact_level": 3,
        "tags": ["us", "capitol_riot", "politics"],
        "source": "manual_curation"
    },
    {
        "event_date": "2021-03-11",
        "event_type": "economic_crisis",
        "title": "US Passes $1.9 Trillion American Rescue Plan",
        "description": "President Biden signs massive new stimulus bill, distributing $1,400 checks and boosting unemployment benefits.",
        "impact_level": 4,
        "tags": ["stimulus", "us", "biden", "fiscal"],
        "source": "manual_curation"
    },
    {
        "event_date": "2021-09-20",
        "event_type": "economic_crisis",
        "title": "Evergrande Debt Crisis Panics Markets",
        "description": "Concerns over the potential collapse of Chinese real estate giant Evergrande trigger global market selloffs.",
        "impact_level": 4,
        "tags": ["evergrande", "china", "real_estate", "debt"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-03-08",
        "event_type": "market_crash",
        "title": "LME Suspends Nickel Trading After 250% Spike",
        "description": "London Metal Exchange halts nickel trading after short squeeze doubles prices to over $100,000 per ton.",
        "impact_level": 4,
        "tags": ["nickel", "lme", "commodity_crisis"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-05-04",
        "event_type": "monetary_policy",
        "title": "Fed Delivers First 50bps Hike Since 2000",
        "description": "Fed raises policy rate by 50bps, intensifying its battle against high inflation.",
        "impact_level": 4,
        "tags": ["fed", "rate_hike", "monetary_tightening"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-07-21",
        "event_type": "monetary_policy",
        "title": "ECB Raises Rates by 50bps (First Hike in 11 Years)",
        "description": "ECB raises rates by 50bps, ending negative interest rates, and launches new bond-purchase tool.",
        "impact_level": 4,
        "tags": ["ecb", "rate_hike", "eurozone"],
        "source": "manual_curation"
    },
    {
        "event_date": "2022-10-13",
        "event_type": "inflation",
        "title": "US Core CPI Hits 40-Year High of 6.6%",
        "description": "Core inflation accelerates, solidifying expectations for continued aggressive Fed rate hikes.",
        "impact_level": 4,
        "tags": ["inflation", "cpi", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2023-05-01",
        "event_type": "economic_crisis",
        "title": "First Republic Bank Fails",
        "description": "JP Morgan acquires First Republic Bank after regulators seize it, closing the third US bank failure of 2023.",
        "impact_level": 4,
        "tags": ["bank_failure", "banking_crisis", "us"],
        "source": "manual_curation"
    },
    {
        "event_date": "2023-11-01",
        "event_type": "monetary_policy",
        "title": "Fed Pauses Rates for Second Consecutive Meeting",
        "description": "Fed keeps rates at 5.25%-5.50% range, signaling interest rate hiking cycle has likely concluded.",
        "impact_level": 3,
        "tags": ["fed", "pause", "monetary_policy"],
        "source": "manual_curation"
    },
    {
        "event_date": "2024-03-05",
        "event_type": "economic_crisis",
        "title": "Gold Breaks Record High Past $2,100",
        "description": "Gold prices rally past $2,100 per ounce, driven by central bank purchases and interest rate cut expectations.",
        "impact_level": 4,
        "tags": ["gold", "record_price", "rally"],
        "source": "manual_curation"
    },
    {
        "event_date": "2024-08-05",
        "event_type": "market_crash",
        "title": "Yen Carry Trade Unwind (Black Monday 2024)",
        "description": "Japan's Nikkei index falls 12.4% in its largest drop since 1987, sparked by BOJ rate hike and US recession fears.",
        "impact_level": 5,
        "tags": ["yen_carry_trade", "japan", "stocks", "market_crash"],
        "source": "manual_curation"
    },
    {
        "event_date": "2024-10-30",
        "event_type": "economic_crisis",
        "title": "Gold Price Breaks Record High Past $2,780",
        "description": "Gold continues its record-breaking rally, driven by geopolitical concerns and election jitters.",
        "impact_level": 5,
        "tags": ["gold", "record_price", "safe_haven"],
        "source": "manual_curation"
    },
    {
        "event_date": "2025-01-20",
        "event_type": "election",
        "title": "Inauguration of Donald Trump (Second Term)",
        "description": "Donald Trump is inaugurated as the 47th President of the United States, promising new tariffs and trade restrictions.",
        "impact_level": 4,
        "tags": ["us", "trump", "politics"],
        "source": "manual_curation"
    }
]

def get_nearest_price(db_session, target_date, direction='before'):
    """Lookup gold price on target_date or the nearest trading day."""
    if direction == 'before':
        price_row = db_session.query(GoldPrice).filter(
            GoldPrice.currency == "USD",
            GoldPrice.date <= target_date
        ).order_by(desc(GoldPrice.date)).first()
    else:
        price_row = db_session.query(GoldPrice).filter(
            GoldPrice.currency == "USD",
            GoldPrice.date >= target_date
        ).order_by(GoldPrice.date).first()
        
    return price_row.close if price_row else None

def seed_events():
    db = SessionLocal()
    try:
        logger.info("=== Seeding Historical Events ===")
        
        inserted = 0
        updated = 0
        for ev in EVENTS_DATA:
            event_dt = datetime.strptime(ev["event_date"], "%Y-%m-%d").date()
            
            # Check if event already exists
            existing = db.query(HistoricalEvent).filter(
                HistoricalEvent.event_date == event_dt,
                HistoricalEvent.title == ev["title"]
            ).first()
            
            if existing:
                # Update attributes
                existing.description = ev["description"]
                existing.event_type = ev["event_type"]
                existing.impact_level = ev["impact_level"]
                existing.tags = json.dumps(ev["tags"])
                existing.source = ev["source"]
                updated += 1
            else:
                new_event = HistoricalEvent(
                    event_date=event_dt,
                    event_type=ev["event_type"],
                    title=ev["title"],
                    description=ev["description"],
                    impact_level=ev["impact_level"],
                    tags=json.dumps(ev["tags"]),
                    source=ev["source"]
                )
                db.add(new_event)
                inserted += 1
                
        db.commit()
        logger.info(f"Seeded {inserted} new events, updated {updated} existing events.")
        
        # Now compute gold price correlations
        logger.info("=== Calculating Event-Price Correlations ===")
        events = db.query(HistoricalEvent).all()
        
        correlated = 0
        for event in events:
            # 1. Price on event day (or nearest before)
            price_at_event = get_nearest_price(db, event.event_date, direction='before')
            if not price_at_event:
                continue
                
            # 2. Price 7 days later
            price_7d = get_nearest_price(db, event.event_date + timedelta(days=7), direction='before')
            
            # 3. Price 30 days later
            price_30d = get_nearest_price(db, event.event_date + timedelta(days=30), direction='before')
            
            # 4. Price 90 days later
            price_90d = get_nearest_price(db, event.event_date + timedelta(days=90), direction='before')
            
            event.gold_price_at_event = price_at_event
            
            if price_7d:
                event.gold_price_change_7d = ((price_7d - price_at_event) / price_at_event) * 100
            if price_30d:
                event.gold_price_change_30d = ((price_30d - price_at_event) / price_at_event) * 100
            if price_90d:
                event.gold_price_change_90d = ((price_90d - price_at_event) / price_at_event) * 100
                
            correlated += 1
            
        db.commit()
        logger.info(f"Calculated gold price correlations for {correlated} events.")
        logger.info("=== Seeding & Correlation Calculation Complete ===")
        
    except Exception as e:
        logger.exception(f"Error seeding events: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_events()
