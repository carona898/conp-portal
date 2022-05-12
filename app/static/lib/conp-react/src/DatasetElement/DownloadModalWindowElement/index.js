import React from "react";
import * as ReactDOM from "react-dom";
import PropTypes from "prop-types";

const DownloadModalWindowElement = (props) => {
  const { size, zipLocation } = props;

  const close = (event) => {
    $("#downloadModal").modal("hide");
  };

  return ReactDOM.createPortal(
    <div className="modal-content">
      <div className="modal-body">
        <table>
         <tr>
           <td style={{width:"150px"}}>
             <img src="static/img/conp.png" className="text-center" style={{width:"100%"}} alt="CONP logo"/>
           </td>
           <td style={{width:"25px"}}/>
           <td colSpan="41">
             <h4 className="modal-title w-100 text-center" id="modalLongTitle">
               You are about to download a {size} file.
             </h4>
             <h4 className="modal-title w-100 text-center" id="modalLongTitle">Are you sure?</h4>
           </td>
         </tr>
       </table>
      </div>
      <div className="modal-footer">
       <div className="btn-group btn-group-lg" style={{width:"100%"}}>
         <button
           type="button"
           className="btn btn-outline-secondary"
           data-dismiss="modal"
           id="cancelDownload"
         >
           Cancel
         </button>
         <a
           href={ zipLocation }
           className="btn btn-secondary"
           id="confirmDownload"
           onClick={close}
         >
           Download
         </a>
       </div>
     </div>
    </div>,
    document.querySelector("#downloadModalDocument")
  );
};

DownloadModalWindowElement.propTypes = {
  size: PropTypes.string,
  zipLocation: PropTypes.string,
};

DownloadModalWindowElement.defaultProps = {
  size: "",
  zipLocation: "",
}

export default DownloadModalWindowElement;
