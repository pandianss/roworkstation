import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import logging

logger = logging.getLogger(__name__)

class AdvancesService:
    """
    Service for processing and analyzing Bank Advances data (Loans).
    Standardized classification based on provided scheme codes and GLs.
    """
    
    # Official Bank Scheme Rules
    SCHEME_RULES = {
        'MUDRA': "SLMUD|CCMUD|CCWMS|TLWMS".split('|'),
        'KCC': "AGKCC|KCCFL|KCCNF|KCCAG|KCCAR|KCCPO|KKISA|KCCHL".split('|'),    # ADDED: KCC schemes
        'SHG': "CCSHG|TLSHG|AGSHG|SHGBL|SHGNF".split('|'),                       # ADDED: SHG schemes
        'HOUSING': "CCSUB|RHDEC|RHISL|RHLGJ|RHNRI|RHNRR|NRITU|NRIGN|RHPMA|RNHBL|RSPH1|RSPH2|RSUBH|STSHL|RGEWS|RHLIG|RGMI1|RGMI2|RSTOP|HOMAD|RMOGR|RAHTN|RBLTN|GNEXT|CRH01|CBH01|CEC01|HLELM|RHLG2|HLKKI|EPLOT|AHPAP|HLKKI".split('|'),
        'VEHICLE': "RPUSH|RTN2W|RVL2W|SVL2W|SVL4W|RGRVL|RGR2W".split('|'),
        'AGRI_JL': "AGEJL|AGTAJ|JLSWS|KCAJL|KCCJL".split('|'),
        'RETAIL_JL': "GLDPC|JLOTH|JLSTF|JLSUV|JLSWL".split('|'),
        'PERSONAL': "DLCLN|RPLOT|RPTOP|RROYL|RSAKH".split('|'),
        'MORTGAGE': "RHNIL|RRVML".split('|'),
        'EDUCATION': "NFEDU|NKEDU|RDREM|REVOC|RSCLR|RVIDJ|RSURA|RSRTA|RSRTB|RNCTD|BSCCS|RSKILL|PMVLS".split('|'),
        'LIQUIRENT': "RLLIQ".split('|'),
        'OTHER_RETAIL': "CCAKS|CCDEP|CDSTF|DLFAP|DLPEN|DLIPL|RABHI|RAKSH|RALNK|RPASS|SBCGA|SBCRP|SBDNC|SBESY|SBFCR|SBGLO|SBGLT|SBLTS|SBNRE|SBNRO|SBPLT|SBPUB|SBSLO|SBSLT|SBSTF|SBSTR|SBSTU|SBTOD|SFCL2|SFDEC|SFNDE|SJLGO|STDPN|STDRL|STFCC|STFFA|STFFL|STFML|STFWL|SURYA|CCCOR|CCSUV|SBKIT|CABCA|CCJLG|CCPRM|CCSFA|CDSPL|CFITL|CMHLS|CSL01|DLFLX|DLPIP|ECL1E|ECL2E|ECL3E|NFMSY|RKSHG|RPSGB|STCOV|STGAD|DLDEP|DLNSC".split('|'),
        'GOV_SCHEME': "AGINF|AHITL|CCITL|TLCBG|CCCBG|TLMAS|CCMAS".split('|'),
        'OTHER_SCHEME': "TLFME|TLKRP|CCKRP|CCFME|TLKVR|CCKVR|TLSAR|CCSAR|TLSRP|CCSRP|TLAGM|CCAGM|TLFSH|CCFSH|CCIFS|TLWSH|AGJLG|CCJLG|AGDRY|AGDTP|TLDTP|TLFPR|CCFPR|AGPLT|CCPLT|AGTPT|TLHKT".split('|'),
        'NPA_GLS': "33750|33850|33950|33999".split('|')
    }
    
    def __init__(self, config_path="data/scheme_config.json"):
        self.config_path = config_path
        self.scheme_map = self._load_scheme_map()
        from src.infrastructure.persistence.advances_repository import AdvancesRepository
        self.repo = AdvancesRepository()
        
    def _load_scheme_map(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_to_db(self, df):
        """Save processed dataframe to persistent store"""
        if df.empty: return None
        
        # Determine Reference Date
        report_date = None
        if 'REPORT_DT' in df.columns:
            latest = str(df['REPORT_DT'].max()).split('.')[0]
            if len(latest) == 8:
                report_date = datetime.strptime(latest, '%Y%m%d').date()
        
        if not report_date:
            report_date = datetime.now().date()
            
        self.repo.save_records(df, report_date)
        return report_date

    def get_stored_data(self, report_dt):
        """Fetch data from DB for a specific date"""
        return self.repo.get_records_by_date(report_dt)

    def get_available_dates(self):
        return self.repo.get_available_dates()

    def process_data(self, file_path_or_buffer):
        """Parse Excel or CSV file and enrich with banking metadata"""
        # Detect file type from name (works for strings and Streamlit UploadedFile)
        is_csv = False
        if isinstance(file_path_or_buffer, str):
            is_csv = file_path_or_buffer.lower().endswith('.csv')
        elif hasattr(file_path_or_buffer, 'name'):
            is_csv = file_path_or_buffer.name.lower().endswith('.csv')

        if is_csv:
            df = pd.read_csv(file_path_or_buffer, low_memory=False)
        else:
            df = pd.read_excel(file_path_or_buffer)
        
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        col_map = {
            'SCHM_CODE': ['SCHEME CODE', 'SCHM_CODE', 'CODE', 'SCHEME', 'SCHEME_CODE'],
            'OPEN_DT': ['OPEN_DT', 'OPEN DATE', 'DATE_OPENED'],
            'NET_BALANCE': ['NET_BALANCE', 'BALANCE', 'CLEAR BALANCE', 'OUTSTANDING', 'BALANCE_AMT'],
            'DOC_AMOUNT': ['DOC_AMOUNT', 'SANCTION LIMIT', 'SANCTION_AMT', 'LIMIT'],
            'PRIORITY_TYPE': ['PRIORITY_TYPE', 'PRIORITY TYPE', 'SEGMENT', 'SECTOR'],
            'GL_SUB_CD': ['GL_SUB_CD', 'GL CODE', 'GL_CODE'],
            'SMA_TYPE': ['SMA_TYPE', 'SMA TYPE', 'SMA_CLASS', 'SMA_STATUS'],
            'AC_NAME': ['AC_NAME', 'ACCOUNT NAME', 'NAME', 'CUSTOMER_NAME'],
            'BRANCH_CODE': ['BRANCH CODE', 'BRANCH_CODE', 'SOL', 'SOL_ID']
        }
        
        normalized_df = pd.DataFrame()
        for target, aliases in col_map.items():
            found = False
            for alias in aliases:
                if alias.upper() in df.columns:
                    normalized_df[target] = df[alias.upper()]
                    found = True
                    break
            if not found:
                normalized_df[target] = None

        for col in df.columns:
            if col not in normalized_df.columns:
                normalized_df[col] = df[col]

        return self._enrich_data(normalized_df)

    def _enrich_data(self, df):
        """Apply business logic based on official constants and requested hierarchy"""
        
        # 1. Date Parsing
        def parse_dt(val):
            if pd.isna(val): return None
            val = str(val).strip()
            try:
                if len(val) == 8 and val.isdigit(): return datetime.strptime(val, '%Y%m%d')
                return pd.to_datetime(val, errors='coerce')
            except (TypeError, ValueError) as exc:
                logger.debug("Could not parse advance open date %r: %s", val, exc)
                return None

        df['OPEN_DT_NORM'] = df['OPEN_DT'].apply(parse_dt)
        # For Portfolio: take NET_BALANCE (normalized to BALANCE_CR)
        df['BALANCE_CR'] = df['NET_BALANCE'].apply(lambda x: abs(float(str(x).replace(',',''))) / 10000000 if pd.notnull(x) else 0)
        # For Sanctions: take DOC_AMOUNT (normalized to LIMIT_CR)
        df['LIMIT_CR'] = df['DOC_AMOUNT'].apply(lambda x: abs(float(str(x).replace(',',''))) / 10000000 if pd.notnull(x) else 0)

        # 2. Scheme Classification (L1: Category | L2: Subdivision | L3: Scheme)
        def classify(row):
            sc = str(row['SCHM_CODE'] or '').strip().upper()
            
            # --- JEWEL LOANS ---
            if sc in self.SCHEME_RULES['AGRI_JL']: return 'Jewel Loan', 'Agri Jewel Loan', sc
            if sc in self.SCHEME_RULES['RETAIL_JL']: return 'Jewel Loan', 'Retail Jewel Loan', sc
            
            # --- CORE RETAIL ---
            if sc in self.SCHEME_RULES['HOUSING']: return 'Core Retail', 'Housing', sc
            if sc in self.SCHEME_RULES['VEHICLE']: return 'Core Retail', 'Vehicle', sc
            if sc in self.SCHEME_RULES['PERSONAL']: return 'Core Retail', 'Personal Loan', sc
            if sc in self.SCHEME_RULES['MORTGAGE']: return 'Core Retail', 'Mortgage', sc
            if sc in self.SCHEME_RULES['EDUCATION']: return 'Core Retail', 'Education', sc
            if sc in self.SCHEME_RULES['LIQUIRENT']: return 'Core Retail', 'Liquirent', sc
            if sc in self.SCHEME_RULES['OTHER_RETAIL']: return 'Core Retail', 'Other Retail', sc
            
            # --- CORE MSME ---
            if sc in self.SCHEME_RULES['MUDRA']: return 'Core MSME', 'Mudra', sc

            # --- CORE AGRI (Govt Sponsored Schemes belong here, NOT in Core MSME) ---
            if sc in self.SCHEME_RULES['GOV_SCHEME']: return 'Core Agri', 'Govt Spon', sc   # FIXED: was 'Core MSME'
            if sc in self.SCHEME_RULES['OTHER_SCHEME']: return 'Core Agri', 'Oth Schematic', sc
            if sc in self.SCHEME_RULES['KCC']: return 'Core Agri', 'KCC', sc
            if sc in self.SCHEME_RULES['SHG']: return 'Core Agri', 'SHG', sc
            
            # Fallback based on Priority Type or existing map
            match = self.scheme_map.get(sc.lower())
            if match: 
                l1 = match.get('l1', 'Others')
                if l1 == 'Agri': l1 = 'Core Agri'
                if l1 == 'Retail': l1 = 'Core Retail'
                if l1 == 'MSME' or l1 == 'SME': l1 = 'Core MSME'
                return l1, match.get('l2', 'Others'), sc
            
            pt = str(row['PRIORITY_TYPE'] or '').upper()
            if 'AGRI' in pt: return 'Core Agri', 'Unclassified Agri', sc
            if 'RETAIL' in pt: return 'Core Retail', 'Unclassified Retail', sc
            if 'SME' in pt or 'MSME' in pt: return 'Core MSME', 'Unclassified MSME', sc
            
            return 'Others', 'Unclassified', sc

        classification = df.apply(classify, axis=1, result_type='expand')
        df['L1_CATEGORY'], df['L2_SECTOR'], df['L3_SCHEME'] = classification[0], classification[1], classification[2]

        # 3. Risk Mapping
        def map_risk(row):
            gl = str(row['GL_SUB_CD'] or '').strip()
            sma = str(row['SMA_TYPE'] or '').strip().upper()
            
            if gl in self.SCHEME_RULES['NPA_GLS']: return 'NPA'
            if 'SMA2' in sma or 'SMA 2' in sma or '2' == sma: return 'SMA-2'
            if 'SMA1' in sma or 'SMA 1' in sma or '1' == sma: return 'SMA-1'
            if 'SMA0' in sma or 'SMA 0' in sma or '0' == sma: return 'SMA-0'
            
            return 'REGULAR'

        df['RISK_CATEGORY'] = df.apply(map_risk, axis=1)
        return df

    def get_summary_stats(self, df):
        """Calculate dashboard-ready metrics and temporal sanction reports"""
        if df.empty: return {}
        
        # Determine Reference Date (Report Date)
        report_date = None
        if 'REPORT_DT' in df.columns:
            # Assuming YYYYMMDD format from CSV sample
            latest = str(df['REPORT_DT'].max()).split('.')[0]
            if len(latest) == 8:
                report_date = datetime.strptime(latest, '%Y%m%d').date()
        
        if not report_date:
            report_date = datetime.now().date()
            
        # Temporal Window Starts
        from src.core.utils.financial_year import get_fy_start, get_quarter_start
        fy_start = get_fy_start(report_date)
        q_start = get_quarter_start(report_date)
        m_start = report_date.replace(day=1)
        
        # Calculate Sanctions (Sanctioned Limit of new accounts in period)
        def get_period_sanctions(period_start):
            mask = df['OPEN_DT_NORM'].dt.date >= period_start
            period_df = df[mask]
            if period_df.empty: return {}
            
            # Group by both L1 (Category) and L2 (Sector)
            res = period_df.groupby(['L1_CATEGORY', 'L2_SECTOR'])['LIMIT_CR'].agg(['sum', 'count']).to_dict('index')
            return res

        m_breakup = get_period_sanctions(m_start)
        q_breakup = get_period_sanctions(q_start)
        fy_breakup = get_period_sanctions(fy_start)

        # Merge breakups into a single structured dict
        all_keys = set(list(m_breakup.keys()) + list(q_breakup.keys()) + list(fy_breakup.keys()))
        sanction_breakup = {}
        for key in all_keys:
            l1, l2 = key
            id_key = f"{l1} - {l2}"
            sanction_breakup[id_key] = {
                'category': l1,
                'subdivision': l2,
                'month_amt': m_breakup.get(key, {}).get('sum', 0),
                'month_count': m_breakup.get(key, {}).get('count', 0),
                'quarter_amt': q_breakup.get(key, {}).get('sum', 0),
                'quarter_count': q_breakup.get(key, {}).get('count', 0),
                'fy_amt': fy_breakup.get(key, {}).get('sum', 0),
                'fy_count': fy_breakup.get(key, {}).get('count', 0)
            }

        summary = {
            'report_date': report_date.strftime("%d.%m.%Y"),
            'total_count': len(df),
            'total_balance_cr': df['BALANCE_CR'].sum(),
            'total_limit_cr': df['LIMIT_CR'].sum(),
            
            'sanction_breakup': sanction_breakup,
            'sanctions': { # Legacy/Total
                'month': sum(v.get('sum', 0) for v in m_breakup.values()),
                'quarter': sum(v.get('sum', 0) for v in q_breakup.values()),
                'fy': sum(v.get('sum', 0) for v in fy_breakup.values())
            },
            
            'by_category': df.groupby('L1_CATEGORY')['BALANCE_CR'].sum().to_dict(),
            'by_sector': df.groupby('L2_SECTOR')['BALANCE_CR'].agg(['count', 'sum']).to_dict('index'),
            'risk_summary': df.groupby('RISK_CATEGORY')['BALANCE_CR'].agg(['count', 'sum']).to_dict('index'),
            
            'top_borrowers': df.nlargest(20, 'BALANCE_CR')[['AC_NAME', 'BALANCE_CR', 'RISK_CATEGORY', 'L2_SECTOR']].to_dict('records'),
            'branch_concentration': df.groupby('BRANCH_CODE')['BALANCE_CR'].sum().nlargest(10).to_dict(),
            'stressed_assets': df[df['RISK_CATEGORY'] != 'REGULAR'].groupby('L2_SECTOR')['BALANCE_CR'].sum().nlargest(5).to_dict()
        }
        return summary

    def generate_branch_wise_sanction_report(self, df, report_date, period='month'):
        """Generate a formatted Excel report of sanctions grouped by branch and category for a specific period."""
        import io
        from src.application.services.master_service import MasterService
        from src.core.utils.financial_year import get_fy_start
        
        # 1. Determine Date Range
        if period == 'fy':
            start_date = get_fy_start(report_date)
            end_date = report_date
            title = "Full FY"
        elif period == 'prev_month':
            # Last day of previous month
            end_date = report_date.replace(day=1) - timedelta(days=1)
            start_date = end_date.replace(day=1)
            title = f"Previous Month ({start_date.strftime('%b %Y')})"
        else: # Default: current month
            start_date = report_date.replace(day=1)
            end_date = report_date
            title = f"Current Month ({start_date.strftime('%b %Y')})"

        # Ensure OPEN_DT_NORM is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['OPEN_DT_NORM']):
            df['OPEN_DT_NORM'] = pd.to_datetime(df['OPEN_DT_NORM'])
            
        mask = (df['OPEN_DT_NORM'].dt.date >= start_date) & (df['OPEN_DT_NORM'].dt.date <= end_date)
        period_df = df[mask].copy()
        
        if period_df.empty:
            return None
            
        # 2. Group by Branch, Category, Sector
        grouped = period_df.groupby(['BRANCH_CODE', 'L1_CATEGORY', 'L2_SECTOR']).agg({
            'LIMIT_CR': ['sum', 'count']
        }).reset_index()
        
        # Flatten columns
        grouped.columns = ['SOL', 'Category', 'Subdivision', 'Sanction Amount (Cr)', 'Account Count']
        
        # 3. Add Branch Names
        ms = MasterService()
        units = ms.get_units_frame()
        # Ensure SOL is string and padded
        grouped['SOL'] = grouped['SOL'].astype(str).str.split('.').str[0].str.zfill(4)
        units['Code'] = units['Code'].astype(str).str.zfill(4)
        
        report_df = grouped.merge(units[['Code', 'Name']], left_on='SOL', right_on='Code', how='left')
        report_df = report_df[['SOL', 'Name', 'Category', 'Subdivision', 'Sanction Amount (Cr)', 'Account Count']]
        report_df.rename(columns={'Name': 'Branch Name'}, inplace=True)
        report_df = report_df.sort_values(['SOL', 'Category'])
        
        # 4. Create Excel
        output = io.BytesIO()
        import datetime as dt # Ensure datetime is available for prev_month logic if not already
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Branch Summary
            sheet_name = f"Sanctions {period.upper()}"[:31] # Excel sheet name limit
            report_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Sheet 2: Account Details
            period_df['SOL'] = period_df['BRANCH_CODE'].astype(str).str.split('.').str[0].str.zfill(4)
            details_df = period_df.merge(units[['Code', 'Name']], left_on='SOL', right_on='Code', how='left')
            details_cols = ['SOL', 'Name', 'AC_NAME', 'FORACID', 'L1_CATEGORY', 'L2_SECTOR', 'LIMIT_CR', 'OPEN_DT_NORM']
            details_df = details_df[details_cols]
            details_df.columns = ['SOL', 'Branch Name', 'Account Name', 'Account No', 'Category', 'Subdivision', 'Amount (Cr)', 'Sanction Date']
            # Format date for Excel
            details_df['Sanction Date'] = details_df['Sanction Date'].dt.strftime("%d.%m.%Y")
            details_df.to_excel(writer, sheet_name='Detailed Sanctions', index=False)
            
        return output.getvalue()
