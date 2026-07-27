from pathlib import Path

from portal_app_v2 import app as v2_api_app


BASE_DIR = Path(__file__).resolve().parent

DASHBOARD_FILE = (
    BASE_DIR
    / "templates"
    / "dq_dashboard_final.html"
)


DASHBOARD_SCRIPT = ""


DASHBOARD_STYLES = """
<style>
    /* Centre the MAADEN logo and move it slightly down. */
    .logo-window {
        width: 110px !important;
        height: 62px !important;
        margin-left: 12px !important;
        transform: translateY(4px);
        overflow: hidden !important;
    }

    .logo-window img {
        width: 280px !important;
        height: auto !important;
        max-width: none !important;
        left: 50% !important;
        top: 50% !important;
        transform: translate(-50%, -50%) !important;
        object-fit: contain !important;
    }

    /* Align and centre all action-button labels. */
    .actions {
        align-items: center !important;
    }

    .actions .button {
        min-width: 190px;
        height: 48px !important;
        min-height: 48px !important;
        padding: 0 18px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: nowrap;
        line-height: 1 !important;
    }

    /* Business Term DQ results sub-window. */
    .panel:has(#businessTermTableBody) .table-wrap {
        max-height: 430px;
        overflow: auto;
        border: 1px solid #293633;
        border-radius: 6px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    /* Failed and not-executed rules sub-window. */
    #failureGrid {
        max-height: 520px;
        overflow-y: auto;
        padding: 4px 10px 4px 4px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    /* Steward mapping sub-window. */
    .panel:has(#mappingTableBody) .table-wrap {
        max-height: 460px;
        overflow: auto;
        border: 1px solid #293633;
        border-radius: 6px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    /* Keep table headings visible while scrolling. */
    .panel:has(#businessTermTableBody) thead th,
    .panel:has(#mappingTableBody) thead th {
        position: sticky;
        top: 0;
        z-index: 6;
        background: #08100f;
        box-shadow: 0 1px 0 #293633;
    }

    /* Scrollbar appearance for Edge and Chrome. */
    .panel:has(#businessTermTableBody)
    .table-wrap::-webkit-scrollbar,

    .panel:has(#mappingTableBody)
    .table-wrap::-webkit-scrollbar,

    #failureGrid::-webkit-scrollbar {
        width: 9px;
        height: 9px;
    }

    .panel:has(#businessTermTableBody)
    .table-wrap::-webkit-scrollbar-track,

    .panel:has(#mappingTableBody)
    .table-wrap::-webkit-scrollbar-track,

    #failureGrid::-webkit-scrollbar-track {
        background: #101817;
        border-radius: 999px;
    }

    .panel:has(#businessTermTableBody)
    .table-wrap::-webkit-scrollbar-thumb,

    .panel:has(#mappingTableBody)
    .table-wrap::-webkit-scrollbar-thumb,

    #failureGrid::-webkit-scrollbar-thumb {
        background: #806f43;
        border: 2px solid #101817;
        border-radius: 999px;
    }

    .panel:has(#businessTermTableBody)
    .table-wrap::-webkit-scrollbar-thumb:hover,

    .panel:has(#mappingTableBody)
    .table-wrap::-webkit-scrollbar-thumb:hover,

    #failureGrid::-webkit-scrollbar-thumb:hover {
        background: #c4aa67;
    }

    .quality-metric-label {
        margin-top: -7px;
        margin-bottom: 12px;
        color: #9caeaa;
        font-size: 10px;
    }

    .compliance-row {
        margin-top: 12px;
        padding: 9px 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        border: 1px solid #293633;
        border-radius: 5px;
        background: #0b1110;
        color: #9caeaa;
        font-size: 10px;
    }

    .compliance-row strong {
        color: #f5f7f6;
        font-size: 12px;
    }

    .compliance-row.low strong {
        color: #ff6969;
    }

    .compliance-row.medium strong {
        color: #f2b84b;
    }

    .compliance-row.high strong {
        color: #8cda45;
    }

    @media (max-width: 850px) {
        .actions {
            width: 100%;
            align-items: stretch !important;
            flex-direction: column;
        }

        .actions .button {
            width: 100%;
        }

        .panel:has(#businessTermTableBody) .table-wrap,
        .panel:has(#mappingTableBody) .table-wrap {
            max-height: 500px;
        }

        #failureGrid {
            max-height: 600px;
        }
    }
</style>
"""