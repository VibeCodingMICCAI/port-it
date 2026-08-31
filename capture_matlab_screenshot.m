function capture_matlab_screenshot
% Capture the original masker.m using the same downloaded prostate arrays.

root_dir = fileparts(mfilename('fullpath'));
data_dir = fullfile(root_dir, 'sample_data');
shape = dlmread(fullfile(data_dir, 'prostate_shape.txt'));

fid = fopen(fullfile(data_dir, 'prostate_mri_int16.raw'), 'r', 'ieee-le');
assert(fid >= 0, 'Run "python download_sample.py" first.');
image_vol = fread(fid, prod(shape), '*int16');
fclose(fid);
image_vol = reshape(image_vol, shape);

fid = fopen(fullfile(data_dir, 'prostate_mask_uint8.raw'), 'r', 'ieee-le');
assert(fid >= 0, 'Run "python download_sample.py" first.');
label_vol = fread(fid, prod(shape), '*uint8');
fclose(fid);
label_vol = reshape(label_vol, shape);

rng(4);
masker(image_vol, label_vol, [], [], false);
drawnow;
fig = findobj('Type', 'figure', 'Name', 'The little masker');
assert(~isempty(fig), 'Masker figure was not created.');

% Move from slice 1 to slice 13, which contains the largest supplied contour.
scroll_callback = get(fig, 'WindowScrollWheelFcn');
scroll_callback(fig, struct('VerticalScrollCount', 12));
set(fig, 'Units', 'pixels', 'Position', [100, 100, 720, 720], ...
    'PaperPositionMode', 'auto');
drawnow;

output_dir = fullfile(root_dir, 'docs', 'images');
if ~exist(output_dir, 'dir'), mkdir(output_dir); end
print(fig, fullfile(output_dir, 'masker-matlab.png'), '-dpng', '-r160');
fprintf('Saved docs/images/masker-matlab.png\n');
close(fig);
end
