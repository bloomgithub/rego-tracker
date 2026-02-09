import streamlit as st
import pandas as pd
from collections import defaultdict
import time
import re
from datetime import datetime

st.title("REGO Tracker")

st.markdown(
    """
    [Access REGO Certificate Data ↗️](https://shared.outlook.inky.com/link?domain=ofgemcloud.sharepoint.com&t=h.eJxVj01PhDAYhP_KhrPb0vLVkhgXCQd1vZms8WLY8lJYoGVLu7ga_7uwN5M5TSbzzPx4zvReuvEaa8cpxVjXEgbRa1ehqSkNjLpVFgk94LRO8YSL97dtrofBqVaUttUqmyawi3_6ZH55Ppls3Hezscw8fR_86fFQKPnxnLVuyF_0Pg6K169szh7g3p-jIo-8u43XrXwFVhtZWxJTP2AEN2AugKSDRWonpdqCAiOvtymkLAXjcS3iMKQsohD4gvKw4kkUHKmgmCQRoZxHnCAW-CGNkxUEK8gsPXN57AGBOrvWXHe3y0jqC3LdGqvW2D_z9w_RlF6m.MEQCIEOqRai7glaEL2pCevL9l0C6I0fzbrxh8TzrRkzXXREFAiAMDq2CSLS_m2zkP5VnuAUaLDHvTnNCuOVvWE-WScap3g)
    """
)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    old_file = st.file_uploader("Previous Report", type=["csv"], key="old")
with col2:
    new_file = st.file_uploader("Latest Report", type=["csv"], key="new")

st.markdown("---")

def parse_cert_id(cert_id):
    if not cert_id or not isinstance(cert_id, str):
        return None
    
    cert_id = cert_id.strip()
    
    if len(cert_id) < 20:
        return None
    
    digit_runs = [(m.start(), m.end(), m.group()) for m in re.finditer(r'\d+', cert_id)]
    
    if not digit_runs:
        return None
    
    seq_run = None
    for start, end, digits in digit_runs:
        if len(digits) >= 8:
            seq_run = (start, end, digits)
            break
    
    if not seq_run:
        seq_run = max(digit_runs, key=lambda x: len(x[2]))
    
    seq_start, seq_end, seq_digits = seq_run
    
    station = cert_id[:seq_start]
    sequence = int(seq_digits[:10].lstrip('0') or '0')
    remainder = cert_id[seq_start + 10:]
    
    period_match = re.match(r'(\d+)([A-Z]+)$', remainder)
    if period_match:
        period = period_match.group(1)
        cert_type = period_match.group(2)
    else:
        period = remainder[:12]
        cert_type = remainder[12:]
    
    return {
        'station': station,
        'sequence': sequence,
        'period': period,
        'cert_type': cert_type,
        'full_id': cert_id
    }

def parse_certificates(df):
    df = df.copy()
    
    parsed_start = df['Start certificate number'].apply(parse_cert_id)
    parsed_end = df['End certificate number'].apply(parse_cert_id)
    
    valid_mask = parsed_start.notna() & parsed_end.notna()
    bad_count = (~valid_mask).sum()
    
    if bad_count > 0:
        st.warning(f"Skipping {bad_count:,} rows that couldn't be parsed")
    
    df = df[valid_mask].copy()
    parsed_start = parsed_start[valid_mask]
    parsed_end = parsed_end[valid_mask]
    
    df['station'] = parsed_start.apply(lambda x: x['station'])
    df['period'] = parsed_start.apply(lambda x: x['period'])
    df['cert_type'] = parsed_start.apply(lambda x: x['cert_type'])
    df['start_seq'] = parsed_start.apply(lambda x: x['sequence'])
    df['end_seq'] = parsed_end.apply(lambda x: x['sequence'])
    
    df['key'] = df['station'] + '_' + df['period'] + '_' + df['cert_type']
    
    return df

def ranges_overlap(start1, end1, start2, end2):
    return start1 <= end2 and start2 <= end1

if old_file and new_file:
    start_time = time.time()
    
    with st.spinner("📂 Loading files..."):
        old_df = parse_certificates(pd.read_csv(old_file))
        new_df_raw = pd.read_csv(new_file)
        time.sleep(0.3)
    
    with st.spinner("🔍 Parsing certificates..."):
        new_df = parse_certificates(new_df_raw)
        st.info(f"Old: {len(old_df):,} rows | New: {len(new_df):,} rows")
        time.sleep(0.3)
    
    with st.spinner("🏗️ Building index..."):
        old_index = defaultdict(list)
        for idx, row in old_df.iterrows():
            old_index[row['key']].append({
                'start': row['start_seq'],
                'end': row['end_seq'],
                'holder': row['Current holder']
            })
        time.sleep(0.3)
    
    with st.spinner("💱 Finding transactions..."):
        transactions = []
        
        for idx, row in new_df.iterrows():
            old_rows = old_index.get(row['key'], [])
            
            for old in old_rows:
                if ranges_overlap(old['start'], old['end'], row['start_seq'], row['end_seq']):
                    if old['holder'] != row['Current holder']:
                        overlap_start = max(old['start'], row['start_seq'])
                        overlap_end = min(old['end'], row['end_seq'])
                        volume = overlap_end - overlap_start + 1
                        
                        transactions.append({
                            'From': old['holder'],
                            'To': row['Current holder'],
                            'Volume': volume
                        })
        time.sleep(0.3)
    
    with st.spinner("📊 Calculating current ownership..."):
        # Filter: April 2025 onwards AND not expired
        new_df_ownership = new_df_raw.copy()
        new_df_ownership['Issue date'] = pd.to_datetime(
            new_df_ownership['Issue date'], 
            errors='coerce',
            dayfirst=True
        )
        
        april_2025 = pd.Timestamp('2025-04-01')
        filtered = new_df_ownership[
            (new_df_ownership['Issue date'] >= april_2025) & 
            (new_df_ownership['Status'] != 'Expired')
        ].copy()
        
        filtered_parsed = parse_certificates(filtered)
        filtered_parsed['volume'] = filtered_parsed['end_seq'] - filtered_parsed['start_seq'] + 1
        
        # Group by Current holder to get total MWh per company
        ownership = filtered_parsed.groupby('Current holder')['volume'].sum().reset_index()
        ownership = ownership.sort_values('volume', ascending=False)
        ownership.columns = ['Company', 'Total MWh']
        time.sleep(0.3)
    
    elapsed = time.time() - start_time
    st.success(f"✅ Analysis completed in {elapsed:.1f}s")
    
    st.markdown("---")
    
    # === TABLE 1: TRANSACTION SUMMARY ===
    st.subheader(f"📊 Transaction Summary ({len(transactions):,} transactions found)")
    
    if transactions:
        tx_df = pd.DataFrame(transactions)
        summary = tx_df.groupby(['From', 'To'])['Volume'].sum().reset_index()
        summary = summary.sort_values('Volume', ascending=False)
        summary.columns = ['Seller', 'Buyer', 'Total MWh']
        summary['Total MWh'] = summary['Total MWh'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(summary, use_container_width=True, height=400)
        st.download_button(
            "📥 Download Transaction Summary", 
            summary.to_csv(index=False), 
            "transaction_summary.csv",
            use_container_width=True
        )
    else:
        st.info("No ownership changes detected between reports")
    
    st.markdown("---")
    
    # === TABLE 2: CURRENT OWNERSHIP BY COMPANY ===
    st.subheader("🏢 Current Ownership by Company")
    st.caption("Non-expired certificates issued since April 2025")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Companies", f"{len(ownership):,}")
    with col2:
        st.metric("Total MWh Held", f"{ownership['Total MWh'].sum():,.0f}")
    
    ownership['Total MWh'] = ownership['Total MWh'].apply(lambda x: f"{x:,.0f}")
    st.dataframe(ownership, use_container_width=True, height=400)
    
    st.download_button(
        "📥 Download Current Ownership", 
        ownership.to_csv(index=False), 
        "current_ownership.csv",
        use_container_width=True
    )
