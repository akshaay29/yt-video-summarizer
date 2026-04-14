import React from 'react';

const VideoPreview = ({ videoId }) => {
  if (!videoId) return null;

  return (
    <div className="w-full max-w-2xl mx-auto mb-8 animate-fade-in shadow-2xl rounded-2xl overflow-hidden border border-gray-800">
      <div className="relative pt-[56.25%]">
        <iframe
          className="absolute top-0 left-0 w-full h-full"
          src={`https://www.youtube.com/embed/${videoId}`}
          title="YouTube video player"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        ></iframe>
      </div>
    </div>
  );
};

export default VideoPreview;
