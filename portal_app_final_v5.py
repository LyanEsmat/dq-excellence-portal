from pathlib import Path

from portal_app_v2 import app as v2_api_app


BASE_DIR = Path(__file__).resolve().parent

DASHBOARD_FILE = (
    BASE_DIR
    / "templates"
    / "dq_dashboard_final.html"
)


DASHBOARD_STYLES = """
<style>
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

    .panel:has(#businessTermTableBody) .table-wrap {
        max-height: 430px;
        overflow: auto;
        border: 1px solid #293633;
        border-radius: 6px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    #failureGrid {
        max-height: 520px;
        overflow-y: auto;
        padding: 4px 10px 4px 4px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    .panel:has(#mappingTableBody) .table-wrap {
        max-height: 460px;
        overflow: auto;
        border: 1px solid #293633;
        border-radius: 6px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    .panel:has(#businessTermTableBody) thead th,
    .panel:has(#mappingTableBody) thead th {
        position: sticky;
        top: 0;
        z-index: 6;
        background: #08100f;
        box-shadow: 0 1px 0 #293633;
    }

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


LOGO_FIX = """
<style>
    .logo-window {
        width: 108px !important;
        height: 64px !important;
        margin-left: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: visible !important;
        transform: translateY(3px) !important;
    }

    .logo-window img {
        position: static !important;
        width: 94px !important;
        height: 54px !important;
        max-width: 94px !important;
        object-fit: contain !important;
        object-position: center !important;
        transform: none !important;
    }
</style>
"""