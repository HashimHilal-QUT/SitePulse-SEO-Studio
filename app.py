import os
import io
import json
import zipfile
import tempfile
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="SEO Auto-Fixer & Optimizer",
    page_icon="🚀",
    layout="wide"
)

# --- Core SEO Engine ---
def analyze_and_fix_html(file_path, root_dir, site_url, default_brand_name):
    """Parses, checks, and updates an HTML file for SEO improvements."""
    relative_path = os.path.relpath(file_path, start=root_dir).replace("\\", "/")
    
    # Calculate canonical URL
    if relative_path.lower() in ["index.html", "index.htm"]:
        page_url = site_url.rstrip('/')
        page_type = "ProfessionalService"
    else:
        clean_path = relative_path.replace(".html", "").replace(".htm", "")
        page_url = f"{site_url.rstrip('/')}/{clean_path}"
        page_type = "Service" if any(k in relative_path.lower() for k in ["service", "solution", "product"]) else "WebPage"

    fixes_applied = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Ensure <head> tag exists
    if not soup.head:
        head_tag = soup.new_tag('head')
        if soup.html:
            soup.html.insert(0, head_tag)
        else:
            soup.insert(0, head_tag)
        fixes_applied.append("Added missing `<head>` tag")

    # 1. Check Title Tag
    title_tag = soup.find('title')
    if not title_tag or not title_tag.text.strip():
        new_title = f"{os.path.basename(clean_path).replace('-', ' ').title()} | {default_brand_name}" if 'clean_path' in locals() else default_brand_name
        if not title_tag:
            title_tag = soup.new_tag('title')
            soup.head.append(title_tag)
        title_tag.string = new_title
        fixes_applied.append(f"Generated missing `<title>`: '{new_title}'")

    page_title = soup.find('title').text.strip()

    # 2. Check Meta Description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if not meta_desc or not meta_desc.get('content', '').strip():
        default_desc = f"Explore {page_title} - Official offerings and technical solutions from {default_brand_name}."
        if not meta_desc:
            meta_desc = soup.new_tag('meta', attrs={'name': 'description', 'content': default_desc})
            soup.head.append(meta_desc)
        else:
            meta_desc['content'] = default_desc
        fixes_applied.append("Added missing `<meta name='description'>` tag")

    page_desc = soup.find('meta', attrs={'name': 'description'})['content']

    # 3. Check Canonical Link
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if not canonical:
        canonical_tag = soup.new_tag('link', rel='canonical', href=page_url)
        soup.head.append(canonical_tag)
        fixes_applied.append(f"Added Canonical Link: `{page_url}`")

    # 4. Check OpenGraph Tags
    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if not og_title:
        soup.head.append(soup.new_tag('meta', property='og:title', content=page_title))
        fixes_applied.append("Added `og:title` tag")

    og_url = soup.find('meta', attrs={'property': 'og:url'})
    if not og_url:
        soup.head.append(soup.new_tag('meta', property='og:url', content=page_url))
        fixes_applied.append("Added `og:url` tag")

    # 5. Fix Image Alt Attributes
    images_fixed = 0
    for img in soup.find_all('img'):
        if not img.get('alt') or not img['alt'].strip():
            img['alt'] = f"{default_brand_name} illustration"
            images_fixed += 1
    if images_fixed > 0:
        fixes_applied.append(f"Added fallback `alt` text to {images_fixed} image(s)")

    # 6. JSON-LD Schema.org Injection
    if not soup.find('script', type='application/ld+json'):
        if page_type == "ProfessionalService":
            schema_data = {
                "@context": "https://schema.org",
                "@type": "ProfessionalService",
                "name": default_brand_name,
                "url": site_url,
                "description": page_desc
            }
        else:
            schema_data = {
                "@context": "https://schema.org",
                "@type": page_type,
                "name": page_title,
                "description": page_desc,
                "url": page_url,
                "publisher": {
                    "@type": "Organization",
                    "name": default_brand_name,
                    "url": site_url
                }
            }
        
        json_string = json.dumps(schema_data, indent=2, ensure_ascii=False)
        script_tag = soup.new_tag('script', type='application/ld+json')
        script_tag.string = f"\n{json_string}\n"
        soup.head.append(script_tag)
        fixes_applied.append(f"Injected `{page_type}` JSON-LD Schema")

    # Save modified HTML back to file if fixes were made
    if fixes_applied:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    return {
        "File Path": relative_path,
        "Page URL": page_url,
        "Status": "Updated & Fixed" if fixes_applied else "Already Optimized",
        "Fixes Count": len(fixes_applied),
        "Details": " | ".join(fixes_applied) if fixes_applied else "No missing tags found"
    }

# --- Streamlit User Interface ---
st.title("🚀 Static Site SEO Optimizer & Schema Injector")
st.write("Upload a `.zip` archive of your website to automatically inspect, fix, and embed search engine optimizations.")

col1, col2 = st.columns(2)

with col1:
    site_url = st.text_input("Production Web URL", "https://barcodestripe.com")

with col2:
    brand_name = st.text_input("Brand / Business Name", "Barcode Stripe")

uploaded_zip = st.file_uploader("Upload Website ZIP File", type=["zip"])

if uploaded_zip and site_url and brand_name:
    if st.button("Run SEO Audit & Apply Fixes", type="primary"):
        with st.spinner("Extracting, analyzing, and applying SEO fixes..."):
            
            # Temporary directory setup
            with tempfile.TemporaryDirectory() as extract_dir, tempfile.TemporaryDirectory() as output_dir:
                
                # Extract original zip file
                zip_path = os.path.join(extract_dir, "uploaded.zip")
                with open(zip_path, "wb") as f:
                    f.write(uploaded_zip.getbuffer())

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Find all HTML files
                report_data = []
                html_count = 0
                
                for root, dirs, files in os.walk(extract_dir):
                    # Ignore hidden technical folders
                    if any(part.startswith('.') for part in root.split(os.sep)):
                        continue
                    
                    for file in files:
                        if file.endswith((".html", ".htm")):
                            html_count += 1
                            file_path = os.path.join(root, file)
                            result = analyze_and_fix_html(file_path, extract_dir, site_url, brand_name)
                            report_data.append(result)

                # Re-zip fixed site directory into memory buffer
                output_zip_path = os.path.join(output_dir, "optimized_website.zip")
                with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                    for root, dirs, files in os.walk(extract_dir):
                        if any(part.startswith('.') for part in root.split(os.sep)) or "uploaded.zip" in files:
                            continue
                        for file in files:
                            if file == "uploaded.zip":
                                continue
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, start=extract_dir)
                            zip_out.write(full_path, arcname=rel_path)

                # Read ZIP bytes for download
                with open(output_zip_path, "rb") as f:
                    zipped_bytes = f.read()

                # --- Render Report and Results ---
                st.success(f"Audit Complete! Analyzed {html_count} HTML pages.")
                
                df = pd.DataFrame(report_data)
                
                # Summary Stats Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Total HTML Pages", len(df))
                m2.metric("Pages Modified", len(df[df["Fixes Count"] > 0]))
                m3.metric("Fully Compliant", len(df[df["Fixes Count"] == 0]))

                # Detailed Report Table
                st.subheader("📊 Detailed Optimization Report")
                st.dataframe(df, use_container_width=True)

                # Download Widget
                st.markdown("### 📥 Download Fixed Website")
                st.download_button(
                    label="Download Optimized Website (.zip)",
                    data=zipped_bytes,
                    file_name="optimized_website.zip",
                    mime="application/zip",
                    type="primary"
                )