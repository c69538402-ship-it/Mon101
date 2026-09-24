import streamlit as st


def show():
    st.markdown(
        """
        <div style="
            display:flex;
            align-items:center;
            gap:10px;
            margin:0 0 12px 0;
        ">
            <div style="
                width:42px;
                height:42px;
                border-radius:12px;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:24px;
                font-weight:800;
                color:white;
                background:linear-gradient(135deg,#2563eb,#7c3aed);
                box-shadow:0 4px 12px rgba(0,0,0,.18);
            ">M</div>
            <div>
                <div style="
                    font-size:20px;
                    font-weight:800;
                    line-height:1.1;
                ">Mon101</div>
                <div style="
                    font-size:12px;
                    opacity:.7;
                ">Calendar & Life Data</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
