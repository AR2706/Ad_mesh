import React, { useEffect, useState } from 'react';

export default function AdMeshPlaceholder({ zone }) {
    const [adData, setAdData] = useState(null);

    useEffect(() => {
        // Fetch ad from the AdMesh Control Plane
        fetch(`http://127.0.0.1:8000/deliver?zone=${zone}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('admesh_token')}` }
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') setAdData(data);
        })
        .catch(err => console.error("AdMesh bypass: ", err));
    }, [zone]);

    if (!adData) return <div style={{ display: 'none' }} />;

    return <div dangerouslySetInnerHTML={{ __html: adData.htmlContent }} />;
}
